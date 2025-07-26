import requests
import pdfplumber
import io
import os
import json

NTFY_TOPIC = "lakewood-beach-water-quality-report"
CLOUDFLARE_WORKER_URL = "https://beach-api.terrencefradet.workers.dev"
CF_API_TOKEN = os.environ.get("CF_API_TOKEN")
PDF_TARGET_BEACH = "Leddy Beach South"
DISPLAY_BEACH_NAME = "Lakewood Beach"
PDF_URL = "https://anrweb.vt.gov/FPR/SwimWater/CityOfBurlingtonPublicReport.aspx"
STATUS_FILE = "current_status.txt"
JSON_OUTPUT_FILE = "status.json"

def determine_status_from_indicator(status_text):
    """Helper function to determine status from the indicator"""
    status_text = str(status_text).lower()
    if "🟢" in status_text or "⚫" in status_text:
        return "green"
    elif "🟡" in status_text:
        return "yellow"
    elif "🔴" in status_text:
        return "red"
    return "unknown"

def validate_status(status, note):
    """Double-check status based on both indicator and note"""
    if "Alert" in note or "Category 2" in note:
        return "yellow"
    elif "Open" in note and status == "green":
        return "green"
    elif "Closed" in note:
        return "red"
    return status

def get_subscribers():
    if not CF_API_TOKEN:
        print("Error: CF_API_TOKEN secret is not set."); return []
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
        print(f"Failed to fetch subscribers from Cloudflare: {e}"); return []

def get_current_status_and_details():
    try:
        response = requests.get(PDF_URL, timeout=20)
        response.raise_for_status()
        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            page = pdf.pages[0]
            table = page.extract_table()
            
            if not table: 
                return {"status": "error", "date": "N/A", "note": "Could not parse PDF table."}
            
            # Find the target beach row
            for row in table:
                if row and PDF_TARGET_BEACH in str(row[0]):
                    # Based on the screenshot format:
                    # Column 0: Beach Name
                    # Column 1: Status (circle indicator)
                    # Column 2: Last Updated
                    # Column 3: Note
                    
                    initial_status = determine_status_from_indicator(row[1])
                    date_updated = str(row[2]).strip() if len(row) > 2 and row[2] else "N/A"
                    note = str(row[3]).strip() if len(row) > 3 and row[3] else ""
                    
                    # Validate and finalize status
                    final_status = validate_status(initial_status, note)
                    
                    # Add debug logging
                    print(f"Raw row data: {row}")
                    print(f"Initial status: {initial_status}")
                    print(f"Parsed date: {date_updated}")
                    print(f"Parsed note: {note}")
                    print(f"Final status: {final_status}")
                    
                    return {
                        "status": final_status,
                        "date": date_updated,
                        "note": note,
                        "beach_name": PDF_TARGET_BEACH
                    }
            
            return {
                "status": "not_found", 
                "date": "N/A", 
                "note": f"{PDF_TARGET_BEACH} not found in report."
            }
            
    except Exception as e:
        print(f"Error fetching or parsing PDF: {e}")
        return {
            "status": "error", 
            "date": "N/A", 
            "note": f"Failed to fetch or process the PDF: {str(e)}"
        }

def send_notifications(message, email_list):
    print(f"Sending notifications for message: {message}")
    requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=message.encode('utf-8'), headers={"Title": "Beach Status Change!"})
    for email in email_list:
        try:
            requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=message.encode('utf-8'), headers={"Title": "Beach Status Change!", "Email": email})
        except Exception as e:
            print(f"Failed to send email to {email}: {e}")

def test_pdf_parsing():
    """Test function to verify parsing"""
    result = get_current_status_and_details()
    print("Test Results:")
    print(json.dumps(result, indent=2))
    return result

def main():
    print("--- Starting Beach Status Check ---")
    try:
        with open(STATUS_FILE, 'r') as f:
            old_status = f.read().strip()
    except FileNotFoundError:
        old_status = "unknown"
    print(f"Last known status: {old_status.upper()}")
    new_data = get_current_status_and_details()
    new_status = new_data["status"]
    print(f"Newly fetched status: {new_status.upper()}")
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
        with open(STATUS_FILE, 'w') as f:
            f.write(new_status)
    else:
        print("Status has not changed or there was an error. No action needed.")
    print("--- Check Complete ---")

if __name__ == "__main__":
    test_pdf_parsing()  # Run test first
    main()             # Then run main program
