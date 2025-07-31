#!/usr/bin/env python
# coding: utf-8

# In[3]:


import pandas as pd
import ollama

# Load your health monitoring CSV
df = pd.read_csv("health_monitoring.csv")

# Aggregate anomalies
def get_health_summary(df):
    summary = ""
    yes_cols = [col for col in df.columns if "(Yes/No)" in col]
    for col in yes_cols:
        abnormal_count = df[col].str.strip().str.lower().value_counts().get("yes", 0)
        summary += f"{col}: {abnormal_count} alerts\n"
    return summary

# Format summary
summary_text = get_health_summary(df)

# Prompt to Ollama model
prompt = f"""You are a health assistant AI. Based on this patient's health summary:
{summary_text}
What proactive care suggestions can you give the caregiver?"""

# Call Ollama API
response = ollama.chat(model="mistral", messages=[
    {"role": "user", "content": prompt}
])

print("🤖 Proactive Care Suggestions:\n")
print(response['message']['content'])

