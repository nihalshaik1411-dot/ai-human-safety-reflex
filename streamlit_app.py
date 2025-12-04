# streamlit_app.py
import streamlit as st
import requests
import os
import time
import pandas as pd

# Configuration
API_BASE = st.secrets.get("API_BASE") if "API_BASE" in st.secrets else os.getenv("API_BASE", "http://localhost:3000")
API_KEY = st.secrets.get("API_KEY") if "API_KEY" in st.secrets else os.getenv("API_KEY", "demo_api_key_please_change")

HEADERS = {"x-api-key": API_KEY, "Content-Type": "application/json"}

st.set_page_config(page_title="AI Human Safety Reflex — Live Dashboard", layout="wide")

st.title("AI Human Safety Reflex — Live Dashboard")

col1, col2 = st.columns([1, 2])

with col1:
    polling = st.number_input("Polling interval (s)", value=2.0, step=0.5, min_value=0.5)
    if st.button("Refresh now"):
        st.experimental_rerun()

    st.markdown("**Event feed**")
    event_container = st.empty()

with col2:
    st.markdown("**Map (approx)**")
    map_container = st.empty()

def fetch_events():
    try:
        r = requests.get(f"{API_BASE}/api/events", headers={"x-api-key": API_KEY})
        return r.json().get("events", [])
    except Exception as e:
        st.error(f"Failed to fetch events: {e}")
        return []

def play_audio_url(url):
    try:
        r = requests.get(url)
        if r.status_code == 200:
            st.audio(r.content)
        else:
            st.warning("Unable to fetch audio")
    except Exception as e:
        st.warning(f"Audio play error: {e}")

# initial fetch
events = fetch_events()

# show latest event on left
if events:
    latest = events[0]
    with event_container:
        st.subheader(f"{latest['type'].upper()} — {latest['createdAt']}")
        st.write(f"Confidence: {latest['confidence']}")
        if latest.get("lat") and latest.get("lon"):
            st.write(f"Location: {latest['lat']}, {latest['lon']}")
        if latest.get("audioKey"):
            # audioKey may be s3 key or local key; presigned playback is needed — call backend /upload/<key> if local, or /api/presign/get not implemented here
            # For simplicity, attempt to use backend's /upload/<key> URL
            audio_url = f"{API_BASE}/upload/{latest['audioKey']}"
            st.markdown("**Audio**")
            try:
                r = requests.get(audio_url)
                if r.status_code == 200:
                    st.audio(r.content)
                else:
                    st.write("Audio not available")
            except Exception:
                st.write("Audio fetch failed")
        if latest.get("videoKey"):
            st.write("Video available (not previewed)")

        # action buttons
        colack, colfp, colforce = st.columns(3)
        if colack.button("Acknowledge"):
            requests.put(f"{API_BASE}/api/events/{latest['id']}/ack", headers=HEADERS, json={"status": "acknowledged"})
            st.success("Acknowledged")
        if colfp.button("False positive"):
            requests.put(f"{API_BASE}/api/events/{latest['id']}/ack", headers=HEADERS, json={"status": "false_positive"})
            st.info("Marked false positive")
        if colforce.button("Force notify"):
            r = requests.post(f"{API_BASE}/api/notify/{latest['id']}", headers=HEADERS)
            st.write(r.json())

# show map
df = []
for e in events:
    if e.get("lat") and e.get("lon"):
        df.append({"lat": e["lat"], "lon": e["lon"], "type": e["type"], "confidence": e["confidence"]})
if df:
    df_map = pd.DataFrame(df)
    df_map = df_map.rename(columns={"lat": "latitude", "lon": "longitude"})
    map_container.map(df_map)

# auto-update loop
st.write("---")
st.write("Event history (recent)")
for e in events[:20]:
    st.write(f"**{e['type'].upper()}** — {e['createdAt']} — Confidence: {e['confidence']}")
