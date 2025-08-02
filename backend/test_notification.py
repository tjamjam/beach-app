#!/usr/bin/env python3
"""
Test script to force a status change and test notifications
"""

import os
import json
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configuration
TEST_MODE = os.environ.get("TEST_MODE", "false").lower() == "true"
TEST_EMAIL = "terrencefradet@gmail.com"
EMAIL_SENDER = os.environ.get("EMAIL_SENDER", "beach-status@yourdomain.com")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))

def test_notification():
    """Test the notification system with a forced status change"""
    print("🧪 Testing notification system...")
    
    # Simulate a status change
    message = "TEST: Lakewood Beach status changed from GREEN to YELLOW. Note: Alert Category 2 BGA level"
    
    # Test mode: only send to test email
    if TEST_MODE:
        print(f"🧪 TEST MODE: Only sending to {TEST_EMAIL}")
        email_list = [TEST_EMAIL]
    else:
        print("⚠️  WARNING: Not in test mode! This would send to all subscribers.")
        return
    
    print(f"Sending test notification: {message}")
    
    # Send to ntfy.sh topic
    try:
        requests.post("https://ntfy.sh/lakewood-beach-water-quality-report", 
                    data=message.encode('utf-8'), 
                    headers={"Title": "TEST: Beach Status Change!"})
        print("✅ Topic notification sent successfully")
    except Exception as e:
        print(f"❌ Failed to send topic notification: {e}")
    
    # Send email
    for email in email_list:
        try:
            if EMAIL_PASSWORD and EMAIL_PASSWORD != "your_email_password":
                msg = MIMEMultipart()
                msg['From'] = EMAIL_SENDER
                msg['To'] = email
                msg['Subject'] = "TEST: Beach Status Change!"
                
                msg.attach(MIMEText(message, 'plain'))
                
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    server.starttls()
                    server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                    server.send_message(msg)
                print(f"✅ Email sent to {email} via Gmail SMTP")
            else:
                print(f"⚠️  Email notification prepared for {email} (no SMTP configured)")
            
        except Exception as e:
            print(f"❌ Failed to send email to {email}: {e}")
    
    print("🧪 Test complete!")

if __name__ == "__main__":
    test_notification() 