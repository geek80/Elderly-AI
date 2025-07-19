import pandas as pd
import streamlit as st
import schedule
import time
from datetime import datetime
import threading

# =====================
# Reminder Agent
# =====================
def load_reminders():
    try:
        df = pd.read_csv("daily_reminder.csv")
        if "Time" not in df.columns or "Task" not in df.columns:
            st.error("Reminder CSV must contain 'Time' and 'Task' columns.")
            return pd.DataFrame()
        return df
    except Exception as e:
        st.error(f"Error loading reminder CSV: {e}")
        return pd.DataFrame()

def run_reminder_agent():
    df = load_reminders()
    if df.empty:
        return
    df['Time'] = df['Time'].astype(str).str.strip()

    def job(task):
        st.write(f"🔔 Reminder: {task} (at {datetime.now().strftime('%H:%M')})")

    for _, row in df.iterrows():
        try:
            schedule.every().day.at(row['Time']).do(job, row['Task'])
        except:
            continue

    def run_schedule():
        while True:
            schedule.run_pending()
            time.sleep(1)

    t = threading.Thread(target=run_schedule)
    t.daemon = True
    t.start()

# =====================
# Health Summary Agent
# =====================
def run_health_agent():
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
            df[col] = df[col].astype(str).str.strip().str.lower().map({'yes': 1, 'no': 0}).fillna(0)

        summary = df.groupby('Device-ID/User-ID')[threshold_cols].sum()
        st.subheader("📊 Health Summary Agent")
        st.dataframe(summary)
    except Exception as e:
        st.error(f"Health Summary Agent Error: {e}")

# =====================
# Safety Monitoring Agent
# =====================
def run_safety_agent():
    try:
        df = pd.read_csv("safety_monitoring.csv")
        df = df.dropna(axis=1, how='all')  # Remove unnamed columns

        if 'Fall Detected (Yes/No)' in df.columns:
            df['Fall Detected (Yes/No)'] = df['Fall Detected (Yes/No)'].astype(str).str.lower().map({'yes': 1, 'no': 0}).fillna(0)
        if 'Alert Triggered (Yes/No)' in df.columns:
            df['Alert Triggered (Yes/No)'] = df['Alert Triggered (Yes/No)'].astype(str).str.lower().map({'yes': 1, 'no': 0}).fillna(0)

        summary = df.groupby('Device-ID/User-ID')[['Fall Detected (Yes/No)', 'Alert Triggered (Yes/No)']].sum()
        st.subheader("🛡️ Safety Monitoring Agent")
        st.dataframe(summary)
    except Exception as e:
        st.error(f"Safety Agent Error: {e}")

# =====================
# Streamlit UI
# =====================
st.title("👵 Multi-Agent Elderly Care AI System")
st.sidebar.header("🧠 Select Agent")
agent = st.sidebar.radio("Choose Agent:", ["Reminder Agent", "Health Summary", "Safety Monitoring"])

if agent == "Reminder Agent":
    st.subheader("⏰ Reminder Agent")
    run_reminder_agent()
    st.success("Reminder Agent is running. Keep this window open!")

elif agent == "Health Summary":
    run_health_agent()

elif agent == "Safety Monitoring":
    run_safety_agent()
