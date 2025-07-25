import requests
import pdfplumber
import io
import os

# --- CONFIGURATION ---
NTFY_TOPIC = "lakewood-beach-water-quality-report"  # Your secret topic

# --- NEW: PIPEDREAM CONFIGURATION ---
# The ID of your Data Store, copied from the Pipedream URL
DATA_STORE_ID = "ds_REu3MVg" 
# The API key will be read from GitHub Secrets, not written here
PIPEDREAM_API_KEY = os.environ.get("PIPEDREAM_API_KEY")
# --- END NEW CONFIGURATION ---

PDF_URL = "https://anrweb.vt.gov/FPR/SwimWater/CityOfBurlingtonPublicReport.aspx"
TARGET_BEACH = "Leddy Beach South"
STATUS_FILE = "current_status.txt"

def get_subscribers():
    """Fetches the list of emails from the Pipedream Data Store."""
    if not PIPEDREAM_API_KEY:
        print("Error: PIPEDREAM_API_KEY secret is not set.")
        return []

    print("Fetching subscriber list from Pipedream...")
    try:
        # Pipedream Data Stores have a specific API endpoint to get a key's value
        url = f"https://api.pipedream.com/v1/data/{DATA_STORE_ID}/subscriber_list"
        headers = {
            "Authorization": f"Bearer {PIPEDREAM_API_KEY}"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Raise an exception for bad status codes
        
        # The API returns the list directly
        subscribers = response.json()
        print(f"Found {len(subscribers)} subscribers.")
        return subscribers if isinstance(subscribers, list) else []
    except Exception as e:
        print(f"Failed to fetch subscribers from Pipedream: {e}")
        return []

def get_current_status():
    """Fetches and parses the PDF to get the latest status color."""
    # This function remains unchanged
    try:
        response = requests.get(PDF_URL, timeout=20)
        response.raise_for_status()
        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            page = pdf.pages[0]
            table = page.extract_table()
            if not table: return "error"
            for row in table:
                if row and row[0] and TARGET_BEACH in row[0]:
                    status_text = row[3].strip().lower() if len(row) > 3 and row[3] else ""
                    if "open" in status_text: return "green"
                    if "advisory" in status_text: return "yellow"
                    if "closed" in status_text: return "red"
                    return "unknown"
            return "not_found"
    except Exception as e:
        print(f"Error fetching or parsing PDF: {e}")
        return "error"

def send_notifications(message, email_list):
    """Sends push notifications and emails to the fetched list."""
    print(f"Sending notifications for message: {message}")
    
    # First, send a push notification to the main topic (for app subscribers)
    requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=message.encode('utf-8'), headers={"Title": "Beach Status Change!"})
    
    # Then, loop through the email list from Pipedream and send emails
    for email in email_list:
        try:
            requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=message.encode('utf-8'), headers={"Title": "Beach Status Change!", "Email": email})
        except Exception as e:
            print(f"Failed to send email to {email}: {e}")

def main():
    print("--- Starting Beach Status Check ---")
    try:
        with open(STATUS_FILE, 'r') as f:
            old_status = f.read().strip()
    except FileNotFoundError:
        old_status = "unknown"
    print(f"Last known status: {old_status.upper()}")

    new_status = get_current_status()
    print(f"Newly fetched status: {new_status.upper()}")

    if new_status != "error" and new_status != old_status:
        print("Status has changed! Fetching subscribers and sending notifications.")
        
        # Get the live email list from Pipedream
        subscriber_emails = get_subscribers()
        
        message = f"Leddy Beach South status changed from {old_status.upper()} to {new_status.upper()}."
        send_notifications(message, subscriber_emails)
        
        with open(STATUS_FILE, 'w') as f:
            f.write(new_status)
    else:
        print("Status has not changed or there was an error. No action needed.")
    print("--- Check Complete ---")

if __name__ == "__main__":
    main()
