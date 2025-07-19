#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import streamlit as st
import schedule
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="Daily Reminder Agent", layout="centered")

st.title("📅 Daily Reminder Agent")

# Upload CSV
uploaded_file = st.file_uploader("Upload your daily_reminder.csv", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    df = df.drop(columns=[col for col in df.columns if "Unnamed" in col])
    df["Scheduled Time"] = pd.to_datetime(df["Scheduled Time"], format="%H:%M:%S", errors='coerce').dt.time
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors='coerce')

    st.success("✅ Reminders loaded!")

    pending_reminders = df[df["Reminder Sent (Yes/No)"].str.strip().str.lower() == "no"]

    logs = []

    def send_reminder(user_id, reminder_type, scheduled_time):
        msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Reminder for User {user_id}: {reminder_type} (Scheduled at {scheduled_time})"
        logs.append(msg)

    if st.button("📣 Run Reminder Agent (5 min)"):
        schedule.clear()
        for _, row in pending_reminders.iterrows():
            try:
                time_str = row["Scheduled Time"].strftime("%H:%M")
                schedule.every().day.at(time_str).do(
                    send_reminder, row["Device-ID/User-ID"], row["Reminder Type"], time_str
                )
            except:
                continue

        end_time = datetime.now() + timedelta(minutes=5)
        with st.spinner("⏳ Running reminders for 5 minutes..."):
            while datetime.now() < end_time:
                schedule.run_pending()
                time.sleep(1)

        st.success("✅ Finished running reminder agent!")
        st.write("### Log Output")
        for log in logs:
            st.write(log)


# In[ ]:

import pandas as pd
import streamlit as st

def daily_health_summary():
    st.header("🩺 Daily Health Summary Agent")
    try:
        df = pd.read_csv("health_monitoring.csv")

        threshold_cols = [
            'Heart Rate Below/Above Threshold (Yes/No)',
            'Blood Pressure Below/Above Threshold (Yes/No)',
            'Glucose Levels Below/Above Threshold (Yes/No)',
            'SpO₂ Below Threshold (Yes/No)',
            'Alert Triggered (Yes/No)',
            'Caregiver Notified (Yes/No)'
        ]

        for col in threshold_cols:
            df[col] = df[col].apply(lambda x: 1 if str(x).strip().lower() == 'yes' else 0)

        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df['Date'] = df['Timestamp'].dt.date

        summary = df.groupby(['Device-ID/User-ID', 'Date'])[threshold_cols].sum().reset_index()

        st.dataframe(summary)
    except Exception as e:
        st.error(f"Error loading health monitoring data: {e}")
def safety_monitoring_summary():
    st.header("🛡️ Safety Monitoring Agent")
    try:
        df = pd.read_csv("safety_monitoring.csv")

        df = df.replace("-", pd.NA).dropna()

        df['Fall Detected (Yes/No)'] = df['Fall Detected (Yes/No)'].apply(lambda x: 1 if str(x).strip().lower() == 'yes' else 0)
        df['Alert Triggered (Yes/No)'] = df['Alert Triggered (Yes/No)'].apply(lambda x: 1 if str(x).strip().lower() == 'yes' else 0)
        df['Caregiver Notified (Yes/No)'] = df['Caregiver Notified (Yes/No)'].apply(lambda x: 1 if str(x).strip().lower() == 'yes' else 0)

        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df['Date'] = df['Timestamp'].dt.date

        summary = df.groupby(['Device-ID/User-ID', 'Date'])[
            ['Fall Detected (Yes/No)', 'Alert Triggered (Yes/No)', 'Caregiver Notified (Yes/No)']
        ].sum().reset_index()

        st.dataframe(summary)
    except Exception as e:
        st.error(f"Error loading safety monitoring data: {e}")
st.sidebar.title("Multi-Agent System")
agent_choice = st.sidebar.radio("Choose an Agent", ["Reminder Agent", "Daily Health Summary", "Safety Monitoring"])

if agent_choice == "Reminder Agent":
    run_reminder_agent()  # Your existing reminder code
elif agent_choice == "Daily Health Summary":
    daily_health_summary()
elif agent_choice == "Safety Monitoring":
    safety_monitoring_summary()





