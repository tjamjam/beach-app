import requests
import pdfplumber
import io
import os
import json

# --- CONFIGURATION ---
NTFY_TOPIC = "lakewood-beach-water-quality-report"
CLOUDFLARE_WORKER_URL = "https://beach-api.terrencefradet.workers.dev"
CF_API_TOKEN = os.environ.get("CF_API_TOKEN")
PDF_TARGET_BEACH = "Leddy Beach South"
DISPLAY_BEACH_NAME = "Lakewood Beach"
PDF_URL = "https://anrweb.vt.gov/FPR/SwimWater/CityOfBurlingtonPublicReport.aspx"
STATUS_FILE = "current_status.txt"
JSON_OUTPUT_FILE = "status.json" # New file to store all data for the website

def get_subscribers():
    if not CF_API_TOKEN:
        print("Error: CF_API_TOKEN secret is not set.")
        return []
    print("Fetching subscriber list from Cloudflare Worker...")
    try:
        url = f"{CLOUDFLARE_WORKER_URL}/get-subscribers"
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

def get_current_status_and_details():
    """Fetches and parses the PDF to get status, date, and notes."""
    try:
        response = requests.get(PDF_URL, timeout=20)
        response.raise_for_status()
        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            page = pdf.pages[0]
            table = page.extract_table()
            if not table: return {"status": "error", "date": "N/A", "note": "Could not parse PDF table."}
            
            for row in table:
                if row and row[0] and PDF_TARGET_BEACH in row[0]:
                    status_text = row[3].strip().lower() if len(row) > 3 and row[3] else "unknown"
                    color = "unknown"
                    if "open" in status_text: color = "green"
                    elif "advisory" in status_text: color = "yellow"
                    elif "closed" in status_text: color = "red"
                    
                    date_updated = row[1].strip() if len(row) > 1 and row[1] else "N/A"
                    note = row[4].strip() if len(row) > 4 and row[4] else ""
                    
                    return {"status": color, "date": date_updated, "note": note}
            
            # If the loop finishes without finding the beach
            return {"status": "not_found", "date": "N/A", "note": f"{PDF_TARGET_BEACH} not found in report."}
            
    except Exception as e:
        print(f"Error fetching or parsing PDF: {e}")
        return {"status": "error", "date": "N/A", "note": "Failed to fetch or process the PDF."}

def send_notifications(message, email_list):
    print(f"Sending notifications for message: {message}")
    requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=message.encode('utf-8'), headers={"Title": "Beach Status Change!"})
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

    # Get all the new details
    new_data = get_current_status_and_details()
    new_status = new_data["status"]
    print(f"Newly fetched status: {new_status.upper()}")

    # Save all details to the JSON file for the website
    with open(JSON_OUTPUT_FILE, 'w') as f:
        json.dump(new_data, f)
    print(f"Updated {JSON_OUTPUT_FILE} with new data.")

    if new_status != "error" and new_status != old_status:
        print("Status has changed! Fetching subscribers and sending notifications.")
        subscriber_emails = get_subscribers()
        message = f"{DISPLAY_BEACH_NAME} status changed from {old_status.upper()} to {new_status.upper()}."
        if new_data["note"]:
            message += f" Note: {new_data['note']}"
        
        if subscriber_emails:
            send_notifications(message, subscriber_emails)
        else:
            print("No subscribers found. Skipping notification.")
        
        # Update the simple status file for the next run's comparison
        with open(STATUS_FILE, 'w') as f:
            f.write(new_status)
    else:
        print("Status has not changed or there was an error. No action needed.")
    print("--- Check Complete ---")

if __name__ == "__main__":
    main()
