#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Cron job script (save as cron_check_reminders.py)
cron_script = """
import logging
import os
from datetime import datetime
import sqlite3
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

logging.basicConfig(level=logging.INFO)

db_path = "/data/db/elderly_ai.db"

def get_connection():
    return sqlite3.connect(db_path)

def send_reminder_email(user_id, email, reminder_type, scheduled_time):
    if not email:
        logging.warning(f"No email for user_id: {user_id}")
        return False
    message = Mail(
        from_email='noreply@elderlyai.io',
        to_emails=email,
        subject=f'Reminder: {reminder_type} at {scheduled_time}',
        plain_text_content=f'Hi! Your {reminder_type} reminder is due at {scheduled_time}. Stay safe!'
    )
    try:
        sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        response = sg.send(message)
        logging.info(f"Email sent to {email} for {reminder_type}, Status: {response.status_code}")
        return response.status_code == 202
    except Exception as e:
        logging.error(f"Email error for {user_id}: {str(e)}")
        return False

conn = get_connection()
try:
    current_time = datetime.now()
    cursor = conn.execute("SELECT r.id, r.user_id, u.email, r.reminder_type, r.scheduled_time FROM reminders r LEFT JOIN users u ON r.user_id = u.user_id WHERE r.sent='No'")
    reminders = cursor.fetchall()
    logging.info(f"Checking {len(reminders)} unsent reminders at {current_time}")
    for reminder in reminders:
        scheduled_time = datetime.strptime(reminder[4], "%Y-%m-%d %H:%M:%S")
        if scheduled_time > current_time:
            logging.info(f"Future reminder {reminder[3]} at {scheduled_time} queued")
        elif scheduled_time <= current_time:
            user_id, email, reminder_type = reminder[1], reminder[2], reminder[3]
            if send_reminder_email(user_id, email, reminder_type, scheduled_time.strftime("%Y-%m-%d %H:%M")):
                conn.execute("UPDATE reminders SET sent='Yes' WHERE id=?", (reminder[0],))
    conn.commit()
except Exception as e:
    logging.error(f"Reminder check failed: {str(e)}")
finally:
    conn.close()
"""

# Save cron script to file (for local testing or manual run)
with open("cron_check_reminders.py", "w") as f:
    f.write(cron_script)


# In[ ]:




