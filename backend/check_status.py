import requests
import pdfplumber
import io
import os
import json
import csv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone

# Import daily snapshot helper
try:
    from daily_snapshot_helper import should_log_daily_snapshot
except ImportError:
    def should_log_daily_snapshot(beach_name):
        """Fallback function if helper module isn't available"""
        return False

# Try to load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, continue without it
    pass

NTFY_TOPIC = "lakewood-beach-water-quality-report"
CLOUDFLARE_WORKER_URL = "https://beach-api.terrencefradet.workers.dev"
CF_API_TOKEN = os.environ.get("CF_API_TOKEN")
PDF_TARGET_BEACH = "Leddy Beach South"
DISPLAY_BEACH_NAME = "Lakewood Beach"
PDF_URL = "https://anrweb.vt.gov/FPR/SwimWater/CityOfBurlingtonPublicReport.aspx"
STATUS_FILE = "current_status.txt"

# Get the project root directory (one level up from backend)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_OUTPUT_FILE = os.path.join(PROJECT_ROOT, "status.json")

# Email configuration
EMAIL_SENDER = os.environ.get("EMAIL_SENDER", "beach-status@yourdomain.com")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))

# Test mode configuration
TEST_MODE = os.environ.get("TEST_MODE", "false").lower() == "true"
TEST_EMAIL = "terrencefradet@gmail.com"

# This dictionary maps the exact beach name from the PDF to its coordinates.
BEACH_COORDINATES = {
    "North Shore Natural Area": {"lat": 44.5156642, "lon": -73.2691206},
    "Leddy Beach North": {"lat": 44.502334, "lon": -73.255060},
    "Leddy Beach South": {"lat": 44.501457, "lon": -73.252218},
    "North Beach North": {"lat": 44.492299, "lon": -73.241944},
    "North Beach South": {"lat": 44.491225, "lon": -73.237259},
    "Texaco Beach": {"lat": 44.488690, "lon": -73.231108},
    "Blanchard Beach North": {"lat": 44.457661, "lon": -73.224039},
    "Blanchard Beach South": {"lat": 44.456550, "lon": -73.225007},
    "Oakledge Cove": {"lat": 44.454203, "lon": -73.229385},
    "Blodgett Water Access Point": {"lat": 44.465701, "lon": -73.219072}
}


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
        print("Error: CF_API_TOKEN environment variable is not set.")
        print("To fix this, you need to:")
        print("1. Get your CF_API_TOKEN from your Cloudflare Worker secrets")
        print("2. Set it as an environment variable: export CF_API_TOKEN='your_token_here'")
        print("3. Or create a .env file in the backend directory with: CF_API_TOKEN=your_token_here")
        print("4. Or run the script with: CF_API_TOKEN=your_token_here python check_status.py")
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
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print(f"Authentication failed: 401 Unauthorized")
            print("This means the CF_API_TOKEN is either missing, incorrect, or expired.")
            print("Please check your token and try again.")
        else:
            print(f"HTTP Error: {e}")
        return []
    except Exception as e:
        print(f"Failed to fetch subscribers from Cloudflare: {e}")
        return []

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
                        "note": note,
                        "coordinates": BEACH_COORDINATES.get(beach_name)
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
    
    # Test mode: only send to test email
    if TEST_MODE:
        print(f"🧪 TEST MODE: Only sending to {TEST_EMAIL}")
        email_list = [TEST_EMAIL]
    else:
        print(f"Sending notifications to {len(email_list)} subscribers...")
    
    # Send to the ntfy.sh topic (for anyone subscribed to the topic)
    try:
        requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", 
                    data=message.encode('utf-8'), 
                    headers={"Title": "Beach Status Change!"})
        print("Topic notification sent successfully")
    except Exception as e:
        print(f"Failed to send topic notification: {e}")
    
    # Send individual emails to each subscriber using a simple email service
    for email in email_list:
        try:
            # Option 1: Use Gmail SMTP (if credentials are configured)
            if EMAIL_PASSWORD and EMAIL_PASSWORD != "your_email_password":
                # Create a MIME message
                msg = MIMEMultipart()
                msg['From'] = EMAIL_SENDER
                msg['To'] = email
                msg['Subject'] = "Beach Status Change!"
                
                # Attach the message to the MIME message
                msg.attach(MIMEText(message, 'plain'))
                
                # Connect to the SMTP server
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    server.starttls() # Secure the connection
                    server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                    server.send_message(msg)
                print(f"Email sent to {email} via Gmail SMTP")
            else:
                # Option 2: Use a webhook service (placeholder)
                email_data = {
                    "to": email,
                    "subject": "Beach Status Change!",
                    "message": message,
                    "from": "beach-status@yourdomain.com"
                }
                print(f"Email notification prepared for {email} (webhook service)")
            
        except Exception as e:
            print(f"Failed to send email to {email}: {e}")
    
    if not EMAIL_PASSWORD or EMAIL_PASSWORD == "your_email_password":
        print("\nTo enable email sending, you can:")
        print("1. Set up Gmail SMTP: Add EMAIL_SENDER and EMAIL_PASSWORD to your .env file")
        print("2. Use SendGrid: Sign up for free tier and configure API key")
        print("3. Use EmailJS: Set up email service integration")

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

    # 3. --- ENHANCED: HISTORICAL LOGGING ---
    # Option: Log daily snapshots regardless of changes for timeline visualization
    DAILY_LOGGING = os.environ.get("DAILY_LOGGING", "true").lower() == "true"
    
    changes_found = 0
    logged_today = set()
    
    for new_beach_data in all_new_data:
        beach_name = new_beach_data['beach_name']
        # Get the old state for this specific beach, if it exists
        old_beach_data = last_known_states.get(beach_name, {})
        
        # Check if the status OR the note has changed
        status_changed = (new_beach_data.get('status') != old_beach_data.get('status') or 
                         new_beach_data.get('note') != old_beach_data.get('note'))
        
        if status_changed:
            print(f"Change detected for {beach_name}! Logging to history.")
            write_to_history(new_beach_data)
            logged_today.add(beach_name)
            changes_found += 1
        elif DAILY_LOGGING and should_log_daily_snapshot(beach_name):
            print(f"Daily snapshot for {beach_name} - logging to history.")
            write_to_history(new_beach_data)
            logged_today.add(beach_name)
    
    if changes_found == 0 and not DAILY_LOGGING:
        print("No meaningful changes detected in any beach status.")
    elif DAILY_LOGGING:
        print(f"Historical logging complete: {changes_found} changes + {len(logged_today) - changes_found} daily snapshots.")

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
            subscriber_emails = get_subscribers()
            message = f"{DISPLAY_BEACH_NAME} status changed from {old_target_status.upper()} to {new_target_status.upper()}."
            if target_beach_data["note"]: message += f" Note: {target_beach_data['note']}"
            if subscriber_emails: 
                send_notifications(message, subscriber_emails)
            else:
                print("No subscribers found to notify.")
        else:
            print("Status for target beach has not changed.")
            
    print("--- Check Complete ---")


if __name__ == "__main__":
    test_pdf_parsing()  # Run test first
    main()             # Then run main program
