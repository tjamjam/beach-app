import requests
import pdfplumber
import io
import os

# --- CONFIGURATION ---
NTFY_TOPIC = "lakewood-beach-water-quality-report"
CLOUDFLARE_WORKER_URL = "https://beach-api.terrencefradet.workers.dev" # Your Cloudflare URL
CF_API_TOKEN = os.environ.get("CF_API_TOKEN") # The secret token
# --- END CONFIGURATION ---

PDF_TARGET_BEACH = "Leddy Beach South"
DISPLAY_BEACH_NAME = "Lakewood Beach"
PDF_URL = "https://anrweb.vt.gov/FPR/SwimWater/CityOfBurlingtonPublicReport.aspx"
STATUS_FILE = "current_status.txt"

def get_subscribers():
    """Fetches the list of emails from our secure Cloudflare Worker."""
    if not CF_API_TOKEN:
        print("Error: CF_API_TOKEN secret is not set.")
        return []

    print("Fetching subscriber list from Cloudflare Worker...")
    try:
        # We call the SECURE endpoint now
        url = f"{CLOUDFLARE_WORKER_URL}/get-subscribers"
        # We provide the secret token in the headers
        headers = {"X-API-Token": CF_API_TOKEN}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        subscribers = data.get("subscribers", [])
        print(f"Found {len(subscribers)} subscribers.")
        return subscribers
    except Exception as e:
        print(f"Failed to fetch subscribers from Cloudflare: {e}")
        return []

# --- ALL OTHER FUNCTIONS BELOW THIS LINE ARE UNCHANGED ---
def get_current_status():
    # ... (code is correct and unchanged)
    try:
        response = requests.get(PDF_URL, timeout=20)
        response.raise_for_status()
        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            page = pdf.pages[0]
            table = page.extract_table()
            if not table: return "error"
            for row in table:
                if row and row[0] and PDF_TARGET_BEACH in row[0]:
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
    # ... (code is correct and unchanged)
    print(f"Sending notifications for message: {message}")
    requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=message.encode('utf-8'), headers={"Title": "Beach Status Change!"})
    for email in email_list:
        try:
            requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=message.encode('utf-8'), headers={"Title": "Beach Status Change!", "Email": email})
        except Exception as e:
            print(f"Failed to send email to {email}: {e}")

def main():
    # ... (code is correct and unchanged)
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
        subscriber_emails = get_subscribers()
        message = f"{DISPLAY_BEACH_NAME} status changed from {old_status.upper()} to {new_status.upper()}."
        if subscriber_emails:
            send_notifications(message, subscriber_emails)
        else:
            print("No subscribers found. Skipping notification.")
        with open(STATUS_FILE, 'w') as f:
            f.write(new_status)
    else:
        print("Status has not changed or there was an error. No action needed.")
    print("--- Check Complete ---")

if __name__ == "__main__":
    main()
