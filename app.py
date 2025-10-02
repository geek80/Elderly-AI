#!/usr/bin/env python
# coding: utf-8

# In[1]:


import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Connect to database
conn = sqlite3.connect("elderly_ai.db")

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
            conn.execute("""
            INSERT INTO reminders (user_id, timestamp, reminder_type, scheduled_time, sent, acknowledged)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, datetime.now().strftime("%m/%d/%Y %H:%M"), reminder_type,
                  scheduled_time.strftime("%H:%M:%S"), "No", "No"))
            conn.commit()
            st.success(f"Reminder for {reminder_type} added!")

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
            hr_alert = "Yes" if hr < 60 or hr > 100 else "No"
            bp_alert = "Yes" if bp_sys > 140 or bp_dia > 90 else "No"
            glucose_alert = "Yes" if glucose < 70 or glucose > 140 else "No"
            spo2_alert = "Yes" if spo2 < 90 else "No"
            alert_triggered = "Yes" if any([hr_alert == "Yes", bp_alert == "Yes", glucose_alert == "Yes", spo2_alert == "Yes"]) else "No"
            caregiver_notified = "Yes" if alert_triggered == "Yes" else "No"
            conn.execute("""
            INSERT INTO health (user_id, timestamp, heart_rate, hr_alert, bp, bp_alert, glucose, glucose_alert, spo2, spo2_alert, alert_triggered, caregiver_notified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, datetime.now().strftime("%m/%d/%Y %H:%M"), hr, hr_alert,
                  f"{bp_sys}/{bp_dia} mmHg", bp_alert, glucose, glucose_alert, spo2, spo2_alert,
                  alert_triggered, caregiver_notified))
            conn.commit()
            st.success("Vitals saved!")

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
            alert_triggered = "Yes" if fall_detected == "Yes" and inactivity_duration > 90 else "No"
            caregiver_notified = "Yes" if alert_triggered == "Yes" else "No"
            conn.execute("""
            INSERT INTO safety (user_id, timestamp, movement, fall_detected, impact_force, inactivity_duration, location, alert_triggered, caregiver_notified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, datetime.now().strftime("%m/%d/%Y %H:%M"), movement, fall_detected,
                  impact_force, inactivity_duration, location, alert_triggered, caregiver_notified))
            conn.commit()
            st.success("Safety event logged!")

conn.close()


# In[ ]:




