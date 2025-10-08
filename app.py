#!/usr/bin/env python
# coding: utf-8

# Import required libraries
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import sqlite3  # Use pysqlite3 override
import streamlit as st
import os
from datetime import datetime
import pandas as pd
import time

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
    db_path = "/data/elderly_ai.db"  # Verified correct path
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)  # Ensure directory exists
st.write(f"Using database at: {os.path.abspath(db_path)}")

# Initialize or connect to database with retry (for initial setup)
if "conn" not in st.session_state:
    max_retries = 5
    for attempt in range(max_retries):
        try:
            st.session_state.conn = sqlite3.connect(db_path, isolation_level=None)  # Initial connection
            st.success("Database connection established!")
            break
        except sqlite3.OperationalError as e:
            if "unable to open database file" in str(e):
                st.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}. Retrying in 2 seconds...")
                time.sleep(2)
            else:
                st.error(f"DB Error: {str(e)}")
                break
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            break
    else:
        st.error(f"Failed to connect to database after {max_retries} attempts.")
        st.session_state.conn = sqlite3.connect(":memory:", isolation_level=None)  # Fallback
    # Create tables if they don't exist
    try:
        with st.session_state.conn:
            st.session_state.conn.execute("""
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
            st.session_state.conn.execute("""
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
            st.session_state.conn.execute("""
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
        st.success("Database tables initialized or verified.")
    except Exception as e:
        st.error(f"Failed to create tables: {str(e)}")

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
            try:
                # Create a new connection for this operation
                with sqlite3.connect(db_path, isolation_level=None) as new_conn:
                    cursor = new_conn.execute("""
                    INSERT INTO reminders (user_id, timestamp, reminder_type, scheduled_time, sent, acknowledged)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (user_id, datetime.now().strftime("%m/%d/%Y %H:%M"), reminder_type,
                          scheduled_time.strftime("%H:%M:%S"), "No", "No"))
                    new_conn.commit()
                    st.success(f"Reminder for {reminder_type} added! Rows affected: {cursor.rowcount}")
            except Exception as e:
                st.error(f"DB Error: {str(e)}")

    st.subheader("Recent Reminders")
    try:
        # Create a new connection for this query
        with sqlite3.connect(db_path, isolation_level=None) as new_conn:
            cursor = new_conn.execute("SELECT * FROM reminders ORDER BY id DESC LIMIT 5")
            st.write(cursor.fetchall())
    except Exception as e:
        st.error(f"DB Error: {str(e)}")

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
            try:
                # Create a new connection for this operation
                with sqlite3.connect(db_path, isolation_level=None) as new_conn:
                    hr_alert = "Yes" if hr < 60 or hr > 100 else "No"
                    bp_alert = "Yes" if bp_sys > 140 or bp_dia > 90 else "No"
                    glucose_alert = "Yes" if glucose < 70 or glucose > 140 else "No"
                    spo2_alert = "Yes" if spo2 < 90 else "No"
                    alert_triggered = "Yes" if any([hr_alert == "Yes", bp_alert == "Yes", glucose_alert == "Yes", spo2_alert == "Yes"]) else "No"
                    caregiver_notified = "Yes" if alert_triggered == "Yes" else "No"
                    cursor = new_conn.execute("""
                    INSERT INTO health (user_id, timestamp, heart_rate, hr_alert, bp, bp_alert, glucose, glucose_alert, spo2, spo2_alert, alert_triggered, caregiver_notified)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (user_id, datetime.now().strftime("%m/%d/%Y %H:%M"), hr, hr_alert,
                          f"{bp_sys}/{bp_dia} mmHg", bp_alert, glucose, glucose_alert, spo2, spo2_alert,
                          alert_triggered, caregiver_notified))
                    new_conn.commit()
                    st.success(f"Vitals saved! Rows affected: {cursor.rowcount}")
            except Exception as e:
                st.error(f"DB Error: {str(e)}")

    st.subheader("Recent Vitals")
    try:
        # Create a new connection for this query
        with sqlite3.connect(db_path, isolation_level=None) as new_conn:
            cursor = new_conn.execute("SELECT * FROM health ORDER BY id DESC LIMIT 5")
            st.write(cursor.fetchall())
    except Exception as e:
        st.error(f"DB Error: {str(e)}")

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
            try:
                # Create a new connection for this operation
                with sqlite3.connect(db_path, isolation_level=None) as new_conn:
                    alert_triggered = "Yes" if fall_detected == "Yes" and inactivity_duration > 90 else "No"
                    caregiver_notified = "Yes" if alert_triggered == "Yes" else "No"
                    cursor = new_conn.execute("""
                    INSERT INTO safety (user_id, timestamp, movement, fall_detected, impact_force, inactivity_duration, location, alert_triggered, caregiver_notified)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (user_id, datetime.now().strftime("%m/%d/%Y %H:%M"), movement, fall_detected,
                          impact_force, inactivity_duration, location, alert_triggered, caregiver_notified))
                    new_conn.commit()
                    st.success(f"Safety event logged! Rows affected: {cursor.rowcount}")
            except Exception as e:
                st.error(f"DB Error: {str(e)}")

    st.subheader("Recent Safety Events")
    try:
        # Create a new connection for this query
        with sqlite3.connect(db_path, isolation_level=None) as new_conn:
            cursor = new_conn.execute("SELECT * FROM safety ORDER BY id DESC LIMIT 5")
            st.write(cursor.fetchall())
    except Exception as e:
        st.error(f"DB Error: {str(e)}")
