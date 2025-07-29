import requests
import pdfplumber
import io
import os
import json
import csv
from datetime import datetime, timezone

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

def validate_status(initial_status, note):
    """
    Determines the final status color, giving priority to the text in the 'note' column.
    This is more reliable than relying only on the parsed icon.
    """
    # Use lowercase for case-insensitive matching
    note_lower = note.lower()

    # --- NEW, MORE ROBUST LOGIC ---
    if "alert" in note_lower or "category 2" in note_lower:
        return "yellow"
    
    # This is the key fix: We no longer check the initial_status for "Open".
    # If the note says "open", the status is green.
    if "open" in note_lower:
        return "green"
    
    if "closed" in note_lower:
        return "red"
    
    # If the note doesn't contain a clear status keyword,
    # then we can fall back to whatever we parsed from the icon.
    return initial_status

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

def get_all_beach_statuses():
    """
    Scrapes the PDF report and returns a list of dictionaries,
    one for each beach found in the table.
    """
    try:
        response = requests.get(PDF_URL, timeout=20)
        response.raise_for_status()
        
        all_beaches = [] # Initialize an empty list to store all beach data
        
        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            page = pdf.pages[0]
            # Use a slightly more robust setting for table extraction
            table = page.extract_table(table_settings={"vertical_strategy": "lines", "horizontal_strategy": "lines"})
            
            if not table or len(table) < 2: 
                print("Could not parse a valid PDF table.")
                return [] # Return empty list on failure

            # Loop through each row in the table, skipping the header (table[0])
            for row in table[1:]:
                # Basic check to ensure the row has data and a name in the first column
                if not row or not row[0]:
                    continue

                try:
                    beach_name = str(row[0]).strip()
                    # The rest of the parsing logic is the same as before
                    initial_status = determine_status_from_indicator(row[1])
                    date_updated = str(row[2]).strip() if len(row) > 2 and row[2] else "N/A"
                    note = str(row[3]).strip() if len(row) > 3 and row[3] else ""
                    final_status = validate_status(initial_status, note)
                    
                    beach_data = {
                        "beach_name": beach_name,
                        "status": final_status,
                        "date": date_updated,
                        "note": note
                    }
                    all_beaches.append(beach_data)
                except (IndexError, TypeError) as e:
                    print(f"Skipping a malformed row in the PDF table: {row}. Error: {e}")
                    continue

            return all_beaches
            
    except Exception as e:
        print(f"Error fetching or parsing PDF for all beaches: {e}")
        return [] # Return an empty list on critical failure


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
    result = get_all_beach_statuses()
    print("Test Results:")
    print(json.dumps(result, indent=2))
    return result


def write_to_history(beach_data):
    """Appends a new record to the historical data CSV file."""
    # The columns for our historical log
    fieldnames = ['record_timestamp_utc', 'beach_name', 'status', 'last_updated_from_pdf', 'note']
    
    # Get the current time in UTC for our own record-keeping
    record_time = datetime.now(timezone.utc).isoformat()
    
    # Check if the history file exists to decide whether to write headers
    file_exists = os.path.isfile('historical_status.csv')
    
    with open('historical_status.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader() # Write headers only if the file is new
            
        writer.writerow({
            'record_timestamp_utc': record_time,
            'beach_name': beach_data['beach_name'],
            'status': beach_data['status'],
            'last_updated_from_pdf': beach_data['date'],
            'note': beach_data['note']
        })


def main():
    print("--- Starting Beach Status Check ---")
    
    # 1. Load the last known state of ALL beaches from status.json
    last_known_states = {}
    try:
        with open(JSON_OUTPUT_FILE, 'r') as f:
            old_data = json.load(f)
            # Create a dictionary for easy lookup: {'Beach Name': {data}}
            for beach in old_data:
                last_known_states[beach['beach_name']] = beach
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"{JSON_OUTPUT_FILE} not found. Will treat all statuses as new.")

    # 2. Fetch all NEW beach data
    all_new_data = get_all_beach_statuses()
    if not all_new_data:
        print("Failed to retrieve any beach data. Exiting.")
        return

    # 3. --- NEW: HISTORICAL LOGGING ---
    changes_found = 0
    for new_beach_data in all_new_data:
        beach_name = new_beach_data['beach_name']
        # Get the old state for this specific beach, if it exists
        old_beach_data = last_known_states.get(beach_name, {})
        
        # Check if the status OR the note has changed
        if (new_beach_data.get('status') != old_beach_data.get('status') or 
            new_beach_data.get('note') != old_beach_data.get('note')):
            
            print(f"Change detected for {beach_name}! Logging to history.")
            write_to_history(new_beach_data)
            changes_found += 1
    
    if changes_found == 0:
        print("No meaningful changes detected in any beach status.")

    # 4. Write the complete new data to status.json (this happens every run)
    with open(JSON_OUTPUT_FILE, 'w') as f:
        json.dump(all_new_data, f, indent=2)
    print(f"Updated {JSON_OUTPUT_FILE} with data for {len(all_new_data)} beaches.")

    # 5. Handle notifications for the specific target beach (logic is unchanged)
    target_beach_data = next((beach for beach in all_new_data if beach["beach_name"] == PDF_TARGET_BEACH), None)
    if target_beach_data:
        old_target_status = last_known_states.get(PDF_TARGET_BEACH, {}).get('status', 'unknown')
        new_target_status = target_beach_data['status']
        print(f"Last known status for {DISPLAY_BEACH_NAME}: {old_target_status.upper()}")
        print(f"Newly fetched status for {DISPLAY_BEACH_NAME}: {new_target_status.upper()}")
        
        if new_target_status != "error" and new_target_status != old_target_status:
            print("Status for target beach has changed! Sending notifications.")
            # ... (rest of notification logic is the same) ...
            subscriber_emails = get_subscribers()
            message = f"{DISPLAY_BEACH_NAME} status changed from {old_target_status.upper()} to {new_target_status.upper()}."
            if target_beach_data["note"]: message += f" Note: {target_beach_data['note']}"
            if subscriber_emails: send_notifications(message, subscriber_emails)
        else:
            print("Status for target beach has not changed.")
            
    print("--- Check Complete ---")


if __name__ == "__main__":
    test_pdf_parsing()  # Run test first
    main()             # Then run main program
