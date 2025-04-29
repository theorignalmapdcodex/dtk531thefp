![alt text](essentials/images/VitalitySync_Logo.png)

# 💖 VitalitySync 🩺
**Stay Ahead, Stay Healthy** 🌟

VitalitySync is a cutting-edge, real-time health monitoring system designed to empower users with actionable insights into their well-being. By integrating data from the MPU-6050 (accelerometer), MAX30102 (heart rate), and PCT2075 (temperature) sensors, this project leverages AI to provide personalized health advice through a sleek Streamlit dashboard. Developed as part of Duke Technology Innovation’s #DTK531_MIDSEMPROJECT_SPRING2025 by Michael Dankwah Agyeman-Prempeh (M.Eng DTI ‘25), VitalitySync is here to revolutionize health monitoring! 🚀

---

## ✨ Features

- **Real-Time Health Monitoring** 📈  
  Collects live data from MPU-6050, MAX30102, and PCT2075 sensors for continuous tracking.

- **Intuitive Streamlit Dashboard** 🖥️  
  Displays live sensor readings, historical trends, and interesting data insights in a visually appealing interface.

- **AI-Driven Insights** 🤖  
  Uses Gemini AI to provide general health advice based on your sensor data and context.

- **Customizable Experience** 🎨  
  Adjust the theme (Dark/Light), refresh rate, and time range for historical trends to suit your preferences.

- **Interesting Data Highlights** 🔍  
  Automatically detects significant changes, such as heart rate spikes or temperature shifts.

---

## 🛠️ Prerequisites

Before you begin, ensure you have the following:

- **Hardware**:
  - Raspberry Pi (with I2C enabled) 🖥️
  - Sensors:
    - MPU-6050 (I2C address: 0x68) 📏
    - MAX30102 (I2C address: 0x57) ❤️
    - PCT2075 (I2C address: 0x48) 🌡️

- **Software**:
  - Python 3.9+ 🐍
  - Virtual environment (recommended) 📦

---

## ⚙️ Setup Instructions

Follow these steps to set up VitalitySync on your Raspberry Pi:

1. **Clone the Project or Prepare the Directory** 📂  
   Place the project files in a directory, e.g., `~/Desktop/DTK531`. If using a repository, clone it:
   ```bash
   git clone <repository-url>
   cd ~/Desktop/DTK531
   ```

2. **Set Up a Virtual Environment** 🛠️  
   Create and activate a virtual environment to manage dependencies:
   ```bash
   python -m venv themax30102venv
   source ~/Desktop/DTK531/themax30102venv/bin/activate
   ```

3. **Install Dependencies** 📦  
   Install the required Python packages listed in `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```
   > **Note**: Ensure the `heartrate_monitor` library for MAX30102 is either installed via PyPI or available in your project directory as a custom library.

4. **Wire the Sensors** 🔌  
   Connect the sensors to your Raspberry Pi:
   - **MPU-6050**:
     - VCC → 3.3V (Pin 1)
     - GND → Ground (Pin 6)
     - SDA → Pin 3 (GPIO 2)
     - SCL → Pin 5 (GPIO 3)
   - **MAX30102**:
     - VCC → 3.3V (Pin 1)
     - GND → Ground (Pin 6)
     - SDA → Pin 3 (GPIO 2)
     - SCL → Pin 5 (GPIO 3)
   - **PCT2075**:
     - VCC → 3.3V (Pin 1)
     - GND → Ground (Pin 6)
     - SDA → Pin 3 (GPIO 2)
     - SCL → Pin 5 (GPIO 3)
     - A0, A1, A2 → GND (for address 0x48)

5. **Enable I2C on Raspberry Pi** 🛠️  
   Ensure I2C is enabled to communicate with the sensors:
   - Run `sudo raspi-config`, navigate to "Interfacing Options," enable I2C, and reboot.
   - Verify sensor addresses using:
     ```bash
     i2cdetect -y 1
     ```
     Expected addresses: MPU-6050 (0x68), MAX30102 (0x57), PCT2075 (0x48).

---

## 🚀 Usage

Get started with VitalitySync in just two steps!

1. **Run the Data Publisher** 📡  
   This script collects live sensor data and publishes it via MQTT:
   ```bash
   cd ~/Desktop/DTK531
   python generate_healthvalues.py
   ```
   The script will run continuously, collecting data every second until you stop it with `Ctrl+C`. You’ll see output like:
   ```
   MPU-6050 initialized successfully! 🚀
   MAX30102 initialized successfully! ❤️
   PCT2075 initialized successfully! 🌡️
   Published to health_sensor/data (Context: resting): {'Heart_Rate': 73.1, 'Body_Temperature': 25.5, ...}
   ```

2. **Launch the Streamlit Dashboard** 🖼️  
   This script displays the data in a user-friendly web interface:
   ```bash
   streamlit run gain_healthinsightswithllm.py
   ```
   Open the provided URL (e.g., `http://localhost:8501`) in your browser to access the dashboard. Explore live readings, trends, and AI insights!

---

## 📁 Project Structure

Here’s an overview of the key files in VitalitySync:

- `generate_healthvalues.py` 📡  
  Collects and publishes sensor data to MQTT and stores it in SQLite.

- `gain_healthinsightswithllm.py` 🖼️  
  Displays sensor data in a Streamlit UI with AI-driven insights from Gemini.

- `requirements.txt` 📦  
  Lists Python dependencies required to run the project.

- `health_data.db` 🗄️  
  SQLite database storing resting and current sensor values.

- `README.md` 📜  
  This file—your guide to setting up and using VitalitySync!

---

## 🎨 Dashboard Overview

The Streamlit dashboard is designed to be intuitive and customizable, featuring:

- **Live Sensor Readings** 📊  
  Real-time heart rate, temperature, and accelerometer data in styled cards.

- **Interesting Insights** 🔍  
  Highlights significant changes, like heart rate spikes or temperature shifts.

- **Historical Trends** 📈  
  Visualize trends over a selectable time range with smooth line plots.

- **AI-Driven Insights** 🤖  
  Get health advice from Gemini AI based on your data and activity context.

- **Extra Insights** 🔎  
  Ask specific questions about your data for detailed, conversational responses.

- **Customization** ⚙️  
  Toggle between Dark/Light themes and adjust the refresh rate via the sidebar.

---

## 🤝 Contributing

VitalitySync is a project by **Michael Dankwah Agyeman-Prempeh (M.Eng DTI ‘25)** as part of **#DTK531_MIDSEMPROJECT_SPRING2025** at Duke Technology Innovation. I welcome feedback, suggestions, and collaboration to make this project even better! Feel free to reach out to contribute or propose enhancements. Let’s innovate together! 🌟

---

## 📜 License

This project is developed for educational purposes under Duke Technology Innovation. All rights reserved.

---

**Let’s Make a Difference in the World, One Step at a Time!** 💪

*Built with ❤️ by Michael Dankwah Agyeman-Prempeh*