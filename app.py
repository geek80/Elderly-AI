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
    db_base_path = "/data/db"  # Updated mount path per Render support
    db_path = os.path.join(db_base_path, "elderly_ai.db")
    os.makedirs(db_base_path, exist_ok=True)  # Ensure directory exists
    # Create or touch the file to ensure it exists
    try:
        with open(db_path, 'a'):
            os.utime(db_path, None)
        st.write(f"Verified write access to {db_path}")
    except Exception as e:
        st.error(f"Permission test failed: {str(e)}")
st.write(f"Using database at: {os.path.abspath(db_path)}")

# Function to get connection (thread-safe)
def get_connection():
    max_retries = 5
    for attempt in range(max_retries):
        try:
            return sqlite3.connect(db_path, isolation_level=None)
        except sqlite3.OperationalError as e:
            if "unable to open database file" in str(e):
                st.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}. Retrying in 2 seconds...")
                time.sleep(2)
            else:
                st.error(f"DB Error: {str(e)}")
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
        st.success("Tables created or verified.")
        return True
    except Exception as e:
        st.error(f"Table creation failed: {str(e)}")
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

    st.subheader("Recent Reminders")
    conn = get_connection()
    if conn is None:
        st.error("Cannot connect to database.")
    else:
        try:
            cursor = conn.execute("SELECT * FROM reminders ORDER BY id DESC LIMIT 5")
            st.write(cursor.fetchall())
        except Exception as e:
            st.error(f"DB Error: {str(e)}")
        finally:
            conn.close()

# Health Summary Agent Form (simplified)
with tab2:
    st.header("Log Vitals")
    st.write("Vitals form placeholder.")

# Safety Monitoring Agent Form (simplified)
with tab3:
    st.header("Log Safety Event")
    st.write("Safety form placeholder.")
