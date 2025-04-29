import paho.mqtt.client as mqtt
import time
import json
import sqlite3
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

# Default color palette from the VitalitySync image
DEFAULT_COLORS = {
    "background": "#FFFFFF",  # White
    "text": "#2E4A62",  # Dark Blue
    "heading": "#FF6F61",  # Coral
    "resting": "#4A919E",  # Teal
    "changing": "#F4A261",  # Light Orange
    "card_bg": "#4A919E",  # Teal for cards
    "card_text": "#FFFFFF",  # White text on cards
    "insight_bg": "#FF6F61",  # Coral for insights
}

# Custom CSS for styling
def apply_styles(colors):
    st.markdown(f"""
        <style>
        :root {{
            --background: {colors['background']};
            --text: {colors['text']};
            --heading: {colors['heading']};
            --card-bg: {colors['card_bg']};
            --card-text: {colors['card_text']};
            --insight-bg: {colors['insight_bg']};
        }}
        .stApp {{
            background-color: var(--background);
            color: var(--text);
        }}
        h1, h2, h3 {{
            color: var(--heading) !important;
        }}
        .stMetric, .stSelectbox, .stTextInput, .stButton>button, .stExpander {{
            background-color: var(--card-bg) !important;
            color: var(--card-text) !important;
            border-radius: 10px;
        }}
        .stMetric label, .stMetric div[data-testid="stMetricValue"] {{
            color: var(--card-text) !important;  /* Set both label and value to white */
        }}
        .stSelectbox label, .stTextInput label, .stExpander label {{
            color: var(--card-text) !important;  /* Changed to white for visibility on Teal background */
        }}
        .stExpander div[data-testid="stExpanderToggle"] span {{
            color: var(--card-text) !important;  /* Expander header text to white */
        }}
        .stButton>button {{
            background-color: var(--heading) !important;
            border: none;
        }}
        .stPlotlyChart, .stDataFrame {{
            background-color: var(--background);
            border-radius: 10px;
            padding: 10px;
        }}
        .sidebar .sidebar-content {{
            background-color: var(--card-bg);
        }}
        .sidebar .sidebar-content h1, 
        .sidebar .sidebar-content h2, 
        .sidebar .sidebar-content h3 {{
            color: var(--card-text) !important;  /* Sidebar headers to white */
        }}
        .insight-box {{
            background-color: var(--insight-bg);
            padding: 10px;
            border-radius: 10px;
            margin: 10px 0;
            color: var(--card-text);
        }}
        </style>
    """, unsafe_allow_html=True)

# Placeholder for Gemini API (assuming it’s correctly set up)
from gemini_ai_call import *
from gemini_myapi import *

# Importing the necessary functions for the Gemini API LLM Interaction to Work
def __get_gemini_client__() -> genai.GenerativeModel:
    genai.configure(api_key=the_api_key)
    gemini_model = genai.GenerativeModel("gemini-1.5-flash")
    return gemini_model

gemini_model = __get_gemini_client__()

# MQTT setup
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Successfully connected to broker")
        client.subscribe("health_sensor/data")
    else:
        print(f"Connection failed with code {rc}")

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())
    store_current_values(data)
    print(f"Received data (Context: {data['context']}): {data}")

# SQLite functions
def store_current_values(data):
    conn = sqlite3.connect("health_data.db")
    c = conn.cursor()
    timestamp = data["timestamp"]
    context = data["context"]
    for metric, value in data.items():
        if metric not in ["timestamp", "context"]:
            c.execute("INSERT INTO current_values (timestamp, metric, value, context) VALUES (?, ?, ?, ?)", 
                      (timestamp, metric, value, context))
    conn.commit()
    conn.close()

def fetch_resting_values():
    conn = sqlite3.connect("health_data.db")
    c = conn.cursor()
    c.execute("SELECT metric, value FROM resting_values")
    resting = dict(c.fetchall())
    conn.close()
    return resting

def fetch_latest_current_values():
    conn = sqlite3.connect("health_data.db")
    c = conn.cursor()
    c.execute("SELECT metric, value, context FROM current_values WHERE timestamp = (SELECT MAX(timestamp) FROM current_values)")
    latest = c.fetchall()
    conn.close()
    return {metric: (value, context) for metric, value, context in latest}

def fetch_historical_data(metric, time_range_hours):
    conn = sqlite3.connect("health_data.db")
    c = conn.cursor()
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=time_range_hours)
    c.execute("SELECT timestamp, value, context FROM current_values WHERE metric = ? AND timestamp >= ? ORDER BY timestamp", 
              (metric, start_time.isoformat()))
    data = c.fetchall()
    conn.close()
    return pd.DataFrame(data, columns=["Timestamp", "Value", "Context"]).sort_values("Timestamp")

def fetch_recent_data(metric, limit=10):
    conn = sqlite3.connect("health_data.db")
    c = conn.cursor()
    c.execute("SELECT timestamp, value, context FROM current_values WHERE metric = ? ORDER BY timestamp DESC LIMIT ?", 
              (metric, limit))
    data = c.fetchall()
    conn.close()
    return pd.DataFrame(data, columns=["Timestamp", "Value", "Context"]).sort_values("Timestamp")

def get_available_metrics():
    conn = sqlite3.connect("health_data.db")
    c = conn.cursor()
    c.execute("SELECT DISTINCT metric FROM resting_values")
    metrics = [row[0] for row in c.fetchall()]
    conn.close()
    return metrics

# Function to detect interesting data points
def detect_interesting_insights():
    insights = []
    metrics = ["Heart_Rate", "Body_Temperature"]
    for metric in metrics:
        df = fetch_recent_data(metric, 10)
        if len(df) < 2:
            continue
        
        # Calculate the difference between consecutive readings
        df["Diff"] = df["Value"].diff().abs()
        max_diff = df["Diff"].max()
        threshold = {"Heart_Rate": 10, "Body_Temperature": 1}  # Thresholds for significant changes
        
        if metric in threshold and max_diff > threshold[metric]:
            latest_value = df["Value"].iloc[-1]
            timestamp = df["Timestamp"].iloc[-1]
            insights.append(f"Significant change in {metric}: {latest_value:.2f} at {timestamp} (change of {max_diff:.2f})")
    
    return insights

# Streamlit UI
# Sidebar for customization and logo
with st.sidebar:
    st.header("VitalitySync Dashboard")
    st.image("essentials/images/VitalitySync_Logo.png", use_container_width=True)  # Reverted to requested path and parameter
    
    st.subheader("Customize Your Experience")
    theme = st.selectbox("Choose Theme", ["Light", "Dark"], key="theme_select")
    refresh_rate = st.slider("Refresh Rate (seconds)", 1, 10, 2, key="refresh_rate_select")
    
    # Color customization
    st.subheader("Customize Colors")
    heading_color = st.color_picker("Heading Color", DEFAULT_COLORS["heading"], key="heading_color")
    resting_color = st.color_picker("Resting State Color (Graph)", DEFAULT_COLORS["resting"], key="resting_color")
    changing_color = st.color_picker("Changing State Color (Graph)", DEFAULT_COLORS["changing"], key="changing_color")
    
    # Update colors based on user input
    colors = DEFAULT_COLORS.copy()
    colors["heading"] = heading_color
    colors["resting"] = resting_color
    colors["changing"] = changing_color
    
    if theme == "Dark":
        colors["background"] = "#2E4A62"  # Dark Blue
        colors["text"] = "#FFFFFF"  # White
        colors["card_bg"] = "#4A919E"  # Teal
        colors["card_text"] = "#FFFFFF"  # White

# Apply the styles
apply_styles(colors)

# Main content
st.image("essentials/images/VitalitySync_Logo.png", use_container_width=True)  # Reverted to requested path and parameter
st.markdown(f"**Stay Ahead, Stay Healthy** - Reducing hospital wait times by empowering you with real-time health insights and a supportive health buddy.")

# Initialize MQTT client
if "mqtt_client" not in st.session_state:
    st.session_state.mqtt_client = mqtt.Client()
    st.session_state.mqtt_client.on_connect = on_connect
    st.session_state.mqtt_client.on_message = on_message
    st.session_state.mqtt_client.connect("broker.hivemq.com", 1883, 60)
    st.session_state.mqtt_client.loop_start()
    st.write("Connected to MQTT broker and listening for sensor data...")

# Initialize session state for static widgets
if "metric_to_plot" not in st.session_state:
    st.session_state.metric_to_plot = get_available_metrics()[0] if get_available_metrics() else "Heart_Rate"
if "time_range" not in st.session_state:
    st.session_state.time_range = 24

# Static widgets outside the loop
st.header("📈 Historical Trends")
col1, col2 = st.columns([3, 1])
with col1:
    st.session_state.metric_to_plot = st.selectbox("Select Metric to Plot", get_available_metrics(), key="metric_select")
with col2:
    # Let Streamlit manage the session state automatically via the key
    st.slider("Time Range (hours)", 1, 24, 24, key="time_range")

# Main content loop for dynamic updates
placeholder = st.empty()
while True:
    with placeholder.container():
        # Section 1: Live Sensor Readings
        st.header("📊 Live Sensor Readings")
        latest_values = fetch_latest_current_values()
        if latest_values:
            context = list(latest_values.values())[0][1]  # Get context from the latest data
            st.subheader(f"Current Context: {context.capitalize()}")
            
            cols = st.columns(3)
            with cols[0]:
                st.metric("Heart Rate", f"{latest_values.get('Heart_Rate', (0, ''))[0]:.2f} BPM")
            with cols[1]:
                st.metric("Temperature", f"{latest_values.get('Body_Temperature', (0, ''))[0]:.2f} °C")
            with cols[2]:
                accel_x = latest_values.get("Accel_X", (0, ""))[0]
                accel_y = latest_values.get("Accel_Y", (0, ""))[0]
                accel_z = latest_values.get("Accel_Z", (0, ""))[0]
                st.metric("Accelerometer (X, Y, Z)", f"{accel_x:.2f}, {accel_y:.2f}, {accel_z:.2f} g")

        # Section 2: Interesting Insights
        st.header("🔍 Interesting Insights")
        insights = detect_interesting_insights()
        if insights:
            for insight in insights:
                st.markdown(f"<div class='insight-box'>{insight}</div>", unsafe_allow_html=True)
        else:
            st.write("No significant changes detected recently.")

        # Section 3: Historical Trends (Graph Rendering)
        metric_to_plot = st.session_state.metric_to_plot
        time_range = st.session_state.time_range  # Access the value directly
        
        if metric_to_plot:
            # Fetch data for the past time_range hours
            df = fetch_historical_data(metric_to_plot, time_range)
            if not df.empty:
                # For demo: Filter the most recent 60 seconds of data
                df["Timestamp"] = pd.to_datetime(df["Timestamp"])
                latest_time = df["Timestamp"].max()
                start_time = latest_time - timedelta(seconds=60)
                df = df[(df["Timestamp"] >= start_time) & (df["Timestamp"] <= latest_time)]
                
                if not df.empty:
                    # Convert timestamps to seconds relative to the start time
                    df["Seconds"] = (df["Timestamp"] - start_time).dt.total_seconds()
                    
                    # Create the graph
                    fig, ax = plt.subplots(figsize=(10, 5))
                    
                    # Plot with different colors for resting vs. changing states
                    for context in df["Context"].unique():
                        color = colors["resting"] if context == "resting" else colors["changing"]
                        label = f"{metric_to_plot} ({context.capitalize()})"
                        subset = df[df["Context"] == context]
                        sns.lineplot(data=subset, x="Seconds", y="Value", marker="o", color=color, label=label, ax=ax)
                    
                    # Customize the graph
                    ax.set_title(f"{metric_to_plot} Over Last Minute", fontsize=14, pad=15)
                    ax.set_xlabel("Time (seconds)", fontsize=12)
                    ax.set_ylabel(metric_to_plot, fontsize=12)
                    ax.grid(True, linestyle="--", alpha=0.7)
                    ax.legend()
                    plt.xticks(fontsize=10)
                    plt.yticks(fontsize=10)
                    plt.tight_layout()
                    st.pyplot(fig)

        # Section 4: Gemini AI Insights
        st.header("🤖 AI-Driven Health Insights")
        with st.expander("Request Insights", expanded=True):
            with st.form("insights_form"):
                user_input = st.text_input("What would you like to know about your health?", placeholder="Tell me about my health!", key="user_input_insights")
                metrics = st.multiselect("Which metrics?", get_available_metrics(), default=get_available_metrics(), key="metrics_select")
                context = st.selectbox("What were you doing?", ["resting", "running", "walking", "exercising"], key="context_select")
                submit_button = st.form_submit_button("Get Insights")

                if submit_button and user_input.lower() == "tell me about my health!":
                    if not metrics or not context:
                        st.error("Please select both metrics and context!")
                    else:
                        resting_values = fetch_resting_values()
                        current_subset = {k: v[0] for k, v in latest_values.items() if k in metrics}
                        
                        # Structured prompt for LLM
                        prompt = f"""
                        You are Gemini, a friendly health AI assistant.
                        
                        A patient is using a personal health sensor and has provided the following data.
                        
                        Please provide general advice and insights based on this data and the current context. 
                        Compare the user's current health metrics with their resting values and provide structured insights based on the context '{context}'.
                        
                        Structure your response clearly using bullet points for each metric.
                            
                        Do not give medical diagnoses or treatment recommendations.
                        If any values are outside of typical ranges for their current activity, mention that the patient should consult with a healthcare professional.
                        Be respectful and avoid alarming language.

                        Resting Values: {json.dumps(resting_values)}
                        Current Values: {json.dumps(current_subset)}
                        Context: {context}
                        """
                        response = gemini_model.generate_content(prompt).text
                        st.subheader("Gemini's Insights:")
                        st.write(response)

        # Section 5: Extra Insights
        st.header("🔎 Request Extra Insights")
        with st.expander("Ask for More Details", expanded=False):
            with st.form("extra_insights_form"):
                extra_query = st.text_area("Ask a specific question about your health data:", placeholder="E.g., Why did my heart rate spike during running?", key="extra_query_input")
                submit_extra = st.form_submit_button("Get Extra Insights")

                if submit_extra and extra_query:
                    recent_data = {}
                    for metric in get_available_metrics():
                        df = fetch_recent_data(metric, 20)
                        recent_data[metric] = df.to_dict()

                    prompt = f"""
                    You are Gemini, a friendly health AI assistant.
                    
                    A patient is using a personal health sensor and has the following recent data:
                    {json.dumps(recent_data)}
                    
                    The patient has asked the following question: "{extra_query}"
                    
                    Provide a detailed, conversational response to the patient's question. Use the recent data to support your insights. Be clear, respectful, and avoid alarming language. Do not provide medical diagnoses or treatment recommendations. If the data suggests something unusual, recommend consulting a healthcare professional.
                    """
                    response = gemini_model.generate_content(prompt).text
                    st.subheader("Extra Insights:")
                    st.write(response)

    time.sleep(refresh_rate)

# Stop MQTT client when the app is closed
def on_app_close():
    if "mqtt_client" in st.session_state:
        st.session_state.mqtt_client.loop_stop()
        st.session_state.mqtt_client.disconnect()
        print("MQTT client disconnected")

st.on_session_end(on_app_close)