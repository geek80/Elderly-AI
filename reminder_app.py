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




