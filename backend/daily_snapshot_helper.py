#!/usr/bin/env python3
"""
Helper functions for daily snapshot logging
"""

import os
import csv
from datetime import datetime, timezone

def should_log_daily_snapshot(beach_name):
    """
    Check if we should log a daily snapshot for this beach.
    Returns True if no record exists for today for this beach.
    """
    if not os.path.isfile('historical_status.csv'):
        return True
    
    today = datetime.now(timezone.utc).date()
    
    try:
        with open('historical_status.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['beach_name'] == beach_name:
                    # Parse the timestamp
                    record_date = datetime.fromisoformat(row['record_timestamp_utc'].replace('Z', '+00:00')).date()
                    if record_date == today:
                        return False  # Already logged today
    except Exception as e:
        print(f"Error checking daily snapshot for {beach_name}: {e}")
        return True
    
    return True

def backfill_historical_data(days_back=30):
    """
    Backfill historical data with dummy records for testing timeline.
    Creates records for the past N days with mostly green status and some variations.
    """
    from check_status import get_all_beach_statuses, write_to_history
    import random
    from datetime import timedelta
    
    print(f"🔄 Backfilling {days_back} days of historical data...")
    
    # Get current beach list
    current_beaches = get_all_beach_statuses()
    if not current_beaches:
        print("❌ Could not fetch current beach data for backfill")
        return
    
    base_date = datetime.now(timezone.utc) - timedelta(days=days_back)
    
    for day in range(days_back):
        date_for_day = base_date + timedelta(days=day)
        
        for beach in current_beaches:
            # Simulate mostly green with occasional yellow/red
            status_choice = random.choices(
                ['green', 'yellow', 'red'], 
                weights=[85, 12, 3],  # 85% green, 12% yellow, 3% red
                k=1
            )[0]
            
            notes = {
                'green': 'Open',
                'yellow': random.choice(['Alert Category 1 BGA level', 'Advisory posted']),
                'red': random.choice(['Alert Category 3 BGA level', 'Closed due to contamination'])
            }
            
            # Create fake beach data for this day
            fake_beach_data = {
                'beach_name': beach['beach_name'],
                'status': status_choice,
                'date': date_for_day.strftime('%b %d %Y %I:%M%p'),
                'note': notes[status_choice]
            }
            
            # Temporarily override the timestamp in write_to_history
            original_write = write_to_history
            
            def write_with_date(beach_data):
                """Write to history with custom date"""
                fieldnames = ['record_timestamp_utc', 'beach_name', 'status', 'last_updated_from_pdf', 'note']
                file_exists = os.path.isfile('historical_status.csv')
                
                with open('historical_status.csv', 'a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    if not file_exists:
                        writer.writeheader()
                    writer.writerow({
                        'record_timestamp_utc': date_for_day.isoformat(),
                        'beach_name': beach_data['beach_name'],
                        'status': beach_data['status'],
                        'last_updated_from_pdf': beach_data['date'],
                        'note': beach_data['note']
                    })
            
            write_with_date(fake_beach_data)
        
        print(f"📅 Backfilled day {day + 1}/{days_back}: {date_for_day.strftime('%Y-%m-%d')}")
    
    print(f"✅ Backfill complete! Added {days_back * len(current_beaches)} historical records")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "backfill":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        backfill_historical_data(days)
    else:
        print("Usage: python daily_snapshot_helper.py backfill [days]")