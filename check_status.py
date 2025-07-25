import requests
import pdfplumber
import io
import os

# --- CONFIGURATION ---
NTFY_TOPIC = "lakewood-beach-water-quality-report"  # Your secret topic
YOUR_EMAIL = "terrencefradet@gmail.com" # <-- IMPORTANT: REPLACE WITH YOUR ACTUAL EMAIL
# --- END CONFIGURATION ---

PDF_URL = "https://anrweb.vt.gov/FPR/SwimWater/CityOfBurlingtonPublicReport.aspx"
TARGET_BEACH = "Leddy Beach South"
STATUS_FILE = "current_status.txt"

def get_current_status():
    """Fetches and parses the PDF to get the latest status color."""
    try:
        response = requests.get(PDF_URL, timeout=20)
        response.raise_for_status()

        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            if not pdf.pages: return "error"
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

def send_notification(message):
    """Sends a push notification AND an email using ntfy.sh."""
    try:
        # --- THIS IS THE MODIFIED PART ---
        headers = {
            "Title": "Beach Status Change!",
            "Email": YOUR_EMAIL  # <-- This new header tells ntfy to send an email
        }
        # --- END OF MODIFICATION ---
        
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode('utf-8'),
            headers=headers # Pass the updated headers here
        )
        print(f"Notification sent to push/desktop and to email: {message}")
    except Exception as e:
        print(f"Failed to send notification: {e}")

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
        print("Status has changed! Sending notification and updating file.")
        
        message = f"Leddy Beach South status changed from {old_status.upper()} to {new_status.upper()}."
        send_notification(message)
        
        with open(STATUS_FILE, 'w') as f:
            f.write(new_status)
    else:
        print("Status has not changed or there was an error. No action needed.")

    print("--- Check Complete ---")

if __name__ == "__main__":
    main()
