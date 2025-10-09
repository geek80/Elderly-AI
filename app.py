#!/usr/bin/env python
# coding: utf-8

# Import required libraries
import logging
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import sqlite3  # Use pysqlite3 override
import streamlit as st
import os
from datetime import datetime
import pandas as pd
import time

# Set up logging (to file, not UI)
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Senior-friendly styling (WCAG 2.1)
st.markdown("""
<style>
.main {max-width: 100%; padding: 1rem;}
.stButton > button {font-size: 1.2rem; background-color: #007bff; color: white;}
.stTextInput > div > input {font-size: 1.2rem;}
.stSelectbox > div > select {font-size: 1.2rem;}
.stNumberInput > div > input {font-size: 1.2rem;}
</style>
""", unsafe_allow_html=True)

# Define database path with Render Persistent Disk
db_path = "elderly_ai.db"
if os.getenv("RENDER"):
    db_base_path = "/data/db"  # Updated mount path per Render support
    db_path = os.path.join(db_base_path, "elderly_ai.db")
    os.makedirs(db_base_path, exist_ok=True)  # Ensure directory exists
    # Create or touch the file to ensure it exists (log only)
    try:
        with open(db_path, 'a'):
            os.utime(db_path, None)
        logging.info(f"Verified write access to {db_path}")
    except Exception as e:
        logging.error(f"Permission test failed: {str(e)}")

# Function to get connection (thread-safe)
def get_connection():
    max_retries = 5
    for attempt in range(max_retries):
        try:
            return sqlite3.connect(db_path, isolation_level=None)
        except sqlite3.OperationalError as e:
            if "unable to open database file" in str(e):
                logging.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}. Retrying in 2 seconds...")
                time.sleep(2)
            else:
                logging.error(f"DB Error: {str(e)}")
                break
    return None

# Create tables
def create_tables():
    conn = get_connection()
    if conn is None:
        return False
    try:
        with conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                timestamp TEXT,
                reminder_type TEXT,
                scheduled_time TEXT,
                sent TEXT,
                acknowledged TEXT
            )
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                timestamp TEXT,
                heart_rate INTEGER,
                hr_alert TEXT,
                bp TEXT,
                bp_alert TEXT,
                glucose INTEGER,
                glucose_alert TEXT,
                spo2 INTEGER,
                spo2_alert TEXT,
                alert_triggered TEXT,
                caregiver_notified TEXT
            )
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS safety (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                timestamp TEXT,
                movement TEXT,
                fall_detected TEXT,
                impact_force TEXT,
                inactivity_duration INTEGER,
                location TEXT,
                alert_triggered TEXT,
                caregiver_notified TEXT
            )
            """)
        logging.info("Tables created or verified.")
        return True
    except Exception as e:
        logging.error(f"Table creation failed: {str(e)}")
        return False

# Create tables on startup
create_tables()

# Tabs for each agent
tab1, tab2, tab3 = st.tabs(["Reminders", "Health", "Safety"])

# Reminder Agent Form
with tab1:
    st.header("Add Reminder")
    with st.form("reminder_form"):
        user_id = st.text_input("User ID", "U1000")
        reminder_type = st.selectbox("Reminder Type", ["Exercise", "Hydration", "Appointment", "Medication"])
        scheduled_time = st.time_input("Scheduled Time")
        submitted = st.form_submit_button("Add")
        if submitted:
            conn = get_connection()
            if conn is None:
                st.error("Cannot connect to database.")
            else:
                try:
                    cursor = conn.execute("""
                    INSERT INTO reminders (user_id, timestamp, reminder_type, scheduled_time, sent, acknowledged)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (user_id, datetime.now().strftime("%m/%d/%Y %H:%M"), reminder_type,
                          scheduled_time.strftime("%H:%M:%S"), "No", "No"))
                    conn.commit()
                    st.success(f"Reminder for {reminder_type} added! Rows affected: {cursor.rowcount}")
                except Exception as e:
                    st.error(f"DB Error: {str(e)}")
                finally:
                    conn.close()

    # Reminder Notification (adjusted for near-time alerts)
    if "last_check" not in st.session_state:
        st.session_state.last_check = time.time()
    current_time = datetime.now().strftime("%H:%M:%S")
    conn = get_connection()
    if conn:
        try:
            cursor = conn.execute("SELECT * FROM reminders WHERE sent='No'")
            reminders = cursor.fetchall()
            for reminder in reminders:
                scheduled_time = datetime.strptime(reminder[4], "%H:%M:%S").time()
                current_dt = datetime.now().time()
                time_diff = abs((datetime.combine(datetime.today(), scheduled_time) - datetime.combine(datetime.today(), current_dt)).total_seconds())
                if time_diff <= 60:  # Alert within 1 minute
                    st.success(f"Reminder Alert: {reminder[3]} at {reminder[4]} for {reminder[1]}!")
                    conn.execute("UPDATE reminders SET sent='Yes' WHERE id=?", (reminder[0],))
                    conn.commit()
        except Exception as e:
            st.error(f"Reminder check failed: {str(e)}")
        finally:
            conn.close()
    if time.time() - st.session_state.last_check > 60:
        st.session_state.last_check = time.time()

# Health Summary Agent Form
with tab2:
    st.header("Log Vitals")
    with st.form("health_form"):
        user_id = st.text_input("User ID", "U1000")
        hr = st.number_input("Heart Rate (bpm)", min_value=0, max_value=200)
        bp_sys = st.number_input("Systolic BP (mmHg)", min_value=0)
        bp_dia = st.number_input("Diastolic BP (mmHg)", min_value=0)
        glucose = st.number_input("Glucose (mg/dL)", min_value=0)
        spo2 = st.number_input("SpO2 (%)", min_value=0, max_value=100)
        submitted = st.form_submit_button("Save")
        if submitted:
            conn = get_connection()
            if conn is None:
                st.error("Cannot connect to database.")
            else:
                try:
                    hr_alert = "Yes" if hr < 60 or hr > 100 else "No"
                    bp_alert = "Yes" if bp_sys > 140 or bp_dia > 90 else "No"
                    glucose_alert = "Yes" if glucose < 70 or glucose > 140 else "No"
                    spo2_alert = "Yes" if spo2 < 90 else "No"
                    alert_triggered = "Yes" if any([hr_alert == "Yes", bp_alert == "Yes", glucose_alert == "Yes", spo2_alert == "Yes"]) else "No"
                    caregiver_notified = "Yes" if alert_triggered == "Yes" else "No"
                    cursor = conn.execute("""
                    INSERT INTO health (user_id, timestamp, heart_rate, hr_alert, bp, bp_alert, glucose, glucose_alert, spo2, spo2_alert, alert_triggered, caregiver_notified)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (user_id, datetime.now().strftime("%m/%d/%Y %H:%M"), hr, hr_alert,
                          f"{bp_sys}/{bp_dia} mmHg", bp_alert, glucose, glucose_alert, spo2, spo2_alert,
                          alert_triggered, caregiver_notified))
                    conn.commit()
                    st.success(f"Vitals saved! Rows affected: {cursor.rowcount}")
                except Exception as e:
                    st.error(f"DB Error: {str(e)}")
                finally:
                    conn.close()

# Safety Monitoring Agent Form
with tab3:
    st.header("Log Safety Event")
    with st.form("safety_form"):
        user_id = st.text_input("User ID", "U1000")
        movement = st.selectbox("Movement", ["Walking", "Sitting", "Lying", "No Movement"])
        fall_detected = st.selectbox("Fall Detected", ["No", "Yes"])
        impact_force = st.selectbox("Impact Force", ["-", "Low", "Medium", "High"]) if fall_detected == "Yes" else "-"
        inactivity_duration = st.number_input("Inactivity Duration (seconds)", min_value=0) if fall_detected == "Yes" else 0
        location = st.selectbox("Location", ["Kitchen", "Bedroom", "Bathroom", "Living Room"])
        submitted = st.form_submit_button("Save")
        if submitted:
            conn = get_connection()
            if conn is None:
                st.error("Cannot connect to database.")
            else:
                try:
                    alert_triggered = "Yes" if fall_detected == "Yes" and inactivity_duration > 90 else "No"
                    caregiver_notified = "Yes" if alert_triggered == "Yes" else "No"
                    cursor = conn.execute("""
                    INSERT INTO safety (user_id, timestamp, movement, fall_detected, impact_force, inactivity_duration, location, alert_triggered, caregiver_notified)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (user_id, datetime.now().strftime("%m/%d/%Y %H:%M"), movement, fall_detected,
                          impact_force, inactivity_duration, location, alert_triggered, caregiver_notified))
                    conn.commit()
                    st.success(f"Safety event logged! Rows affected: {cursor.rowcount}")
                except Exception as e:
                    st.error(f"DB Error: {str(e)}")
                finally:
                    conn.close()
