#!/usr/bin/env python
# coding: utf-8

import logging
import os
from datetime import datetime
import sqlite3
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Set up logging to stdout for Render Logs
logging.basicConfig(level=logging.INFO)

# Define database path
db_path = "/data/db/elderly_ai.db" if os.getenv("RENDER") else os.path.join(os.getcwd(), "data/db/elderly_ai.db")
logging.info(f"Script started at {datetime.now()}. DB path: {db_path}")

def get_connection():
    logging.info("Attempting DB connection")
    return sqlite3.connect(db_path)

def send_reminder_email(user_id, email, reminder_type, scheduled_time):
    logging.info(f"Attempting to send to {email} for {reminder_type} (user_id: {user_id})")
    if not email:
        logging.warning(f"No email for user_id: {user_id}")
        return False
    scheduled_time_str = scheduled_time.strftime("%Y-%m-%d %H:%M:%S")
    message = Mail(
        from_email='noreply@elderlyai.io',  # Replace with verified sender
        to_emails=email,
        subject=f'Reminder: {reminder_type} at {scheduled_time_str}',
        plain_text_content=f'Hi! Your {reminder_type} reminder is due at {scheduled_time_str}. Stay safe!'
    )
    try:
        api_key = os.getenv('SENDGRID_API_KEY')
        if not api_key:
            logging.error("SENDGRID_API_KEY not found in env vars")
            return False
        logging.info(f"API Key loaded: {api_key[:10]}...")
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        logging.info(f"Email sent to {email} for {reminder_type}, Status: {response.status_code}")
        return response.status_code == 202
    except Exception as e:
        logging.error(f"Email error for {user_id}: {str(e)}")
        return False

if __name__ == "__main__":
    conn = get_connection()
    if conn is None:
        logging.error("Failed to connect to database")
    else:
        try:
            current_time = datetime.now()
            cursor = conn.execute("SELECT r.id, r.user_id, u.email, r.reminder_type, r.scheduled_time FROM reminders r LEFT JOIN users u ON r.user_id = u.user_id WHERE r.sent='No'")
            reminders = cursor.fetchall()
            logging.info(f"Checking {len(reminders)} unsent reminders at {current_time}")
            emails_sent = 0
            for reminder in reminders:
                scheduled_time_str = reminder[4]
                try:
                    # Try full datetime format first
                    scheduled_time = datetime.strptime(scheduled_time_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        # Fall back to time-only format, assume today
                        scheduled_time = datetime.strptime(scheduled_time_str, "%H:%M:%S").replace(
                            year=current_time.year, month=current_time.month, day=current_time.day
                        )
                    except ValueError:
                        logging.error(f"Invalid scheduled_time format for ID {reminder[0]}: {scheduled_time_str}")
                        continue
                time_diff = (scheduled_time - current_time).total_seconds()
                logging.info(f"Reminder ID {reminder[0]}: scheduled {scheduled_time}, diff {time_diff}")
                if -300 <= time_diff <= 300:  # 5-minute window
                    user_id, email, reminder_type = reminder[1], reminder[2], reminder[3]
                    if send_reminder_email(user_id, email, reminder_type, scheduled_time):
                        conn.execute("UPDATE reminders SET sent='Yes' WHERE id=?", (reminder[0],))
                        emails_sent += 1
            logging.info(f"Sent {emails_sent} emails in this run")
            conn.commit()
        except Exception as e:
            logging.error(f"Reminder check failed: {str(e)}")
        finally:
            conn.close()
