import paho.mqtt.client as mqtt
import time
import json
import sqlite3
from datetime import datetime
from mpu6050 import mpu6050
from heartrate_monitor import HeartRateMonitor
import board
import adafruit_pct2075
import random

# # Initialize sensors
try:
    accel_sensor = mpu6050(0x68)  # MPU-6050 for accelerometer
    print("MPU-6050 initialized successfully! 🚀")
except Exception as e:
    print(f"Failed to initialize MPU-6050: {e}")
    exit()

try:
    hr_sensor = HeartRateMonitor()  # MAX30102 for heart rate
    print("MAX30102 initialized successfully! ❤️")
    hr_sensor.start_sensor()  # Start the heart rate sensor thread
    time.sleep(5)  # Allow stabilization
except Exception as e:
    print(f"Failed to initialize MAX30102: {e}")
    exit()

try:
    i2c = board.I2C()  # Uses default I2C pins on Raspberry Pi (SDA: Pin 3, SCL: Pin 5)
    temp_sensor = adafruit_pct2075.PCT2075(i2c)  # PCT2075 for temperature
    print("PCT2075 initialized successfully! 🌡️")
except Exception as e:
    print(f"Failed to initialize PCT2075: {e}")
    exit()

# SQLite setup for storing resting and current values
def init_db():
    conn = sqlite3.connect("health_data.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS resting_values 
                 (metric TEXT PRIMARY KEY, value REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS current_values 
                 (timestamp TEXT, metric TEXT, value REAL, context TEXT)''')
    conn.commit()
    conn.close()

# Store initial resting values (taken as an average over 10 seconds at rest)
def store_resting_values():
    conn = sqlite3.connect("health_data.db")
    c = conn.cursor()
    
    # Collect resting values over 10 seconds
    hr_samples = []
    temp_samples = []
    accel_samples = {"x": [], "y": [], "z": []}
    print("Collecting resting values for 10 seconds... Please remain still.")
    for _ in range(10):
        # Heart Rate
        bpm = hr_sensor.bpm
        if bpm > 0:
            hr_samples.append(bpm)
        
        # Temperature (PCT2075)
        temp = temp_sensor.temperature
        temp_samples.append(temp)
        
        # Accelerometer
        accel_data = accel_sensor.get_accel_data()
        accel_samples["x"].append(accel_data["x"])
        accel_samples["y"].append(accel_data["y"])
        accel_samples["z"].append(accel_data["z"])
        
        time.sleep(1)
    
    # Calculate averages
    resting_data = {
        "Heart_Rate": sum(hr_samples) / len(hr_samples) if hr_samples else 70.0,
        "Body_Temperature": sum(temp_samples) / len(temp_samples) if temp_samples else 25.0,
        "Accel_X": sum(accel_samples["x"]) / len(accel_samples["x"]) if accel_samples["x"] else 0.0,
        "Accel_Y": sum(accel_samples["y"]) / len(accel_samples["y"]) if accel_samples["y"] else 0.0,
        "Accel_Z": sum(accel_samples["z"]) / len(accel_samples["z"]) if accel_samples["z"] else 0.0,
    }
    
    # Store in database
    for metric, value in resting_data.items():
        c.execute("INSERT OR REPLACE INTO resting_values (metric, value) VALUES (?, ?)", (metric, value))
    conn.commit()
    conn.close()
    print("Resting values stored:", resting_data)

def collect_sensor_data(context="resting"):
    # Collect live sensor data
    bpm = hr_sensor.bpm if hr_sensor.bpm > 0 else 70.0  # Fallback if no valid reading
    temp = temp_sensor.temperature  # Read from PCT2075
    accel_data = accel_sensor.get_accel_data()
    
    return {
        "Heart_Rate": bpm,
        "Body_Temperature": temp,
        "Accel_X": accel_data["x"],
        "Accel_Y": accel_data["y"],
        "Accel_Z": accel_data["z"],
        "timestamp": datetime.now().isoformat(),
        "context": context
    }

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

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Successfully connected to broker")
    else:
        print(f"Connection failed with code {rc}")

# Initialize database and resting values
init_db()
store_resting_values()

# Create publisher client
publisher = mqtt.Client()
publisher.on_connect = on_connect
publisher.connect("broker.hivemq.com", 1883, 60)
publisher.loop_start()

try:
    contexts = ["resting", "running", "walking", "exercising"]
    current_context_index = 0
    
    while True:
        if random.randint(1, 5) == 1:
            current_context_index = (current_context_index + 1) % len(contexts)
        
        context = contexts[current_context_index]
        sensor_data = collect_sensor_data(context)
        store_current_values(sensor_data)
        
        topic = "health_sensor/data"
        publisher.publish(topic, json.dumps(sensor_data), qos=1)
        print(f"Published to {topic} (Context: {context}): {sensor_data}")
        time.sleep(1)

except KeyboardInterrupt:
    print("Stopping publisher... User can now request insights.")
    hr_sensor.stop_sensor()
    publisher.loop_stop()
    publisher.disconnect()









# ------- OTHER CODE ---------- #
# import paho.mqtt.client as mqtt
# import time
# import json
# import sqlite3
# from datetime import datetime
# from mpu6050 import mpu6050
# from heartrate_monitor import HeartRateMonitor
# import board
# import adafruit_pct2075
# import random

# # Initialize sensors with error handling
# accel_sensor = None
# hr_sensor = None
# temp_sensor = None
# at_least_one_sensor = False  # Flag to check if at least one sensor initialized

# try:
#     accel_sensor = mpu6050(0x69)  # MPU-6050 for accelerometer
#     print("MPU-6050 initialized successfully! 🚀")
#     at_least_one_sensor = True
# except Exception as e:
#     print(f"Failed to initialize MPU-6050: {e}")
#     accel_sensor = None  # Set to None if initialization fails

# try:
#     hr_sensor = HeartRateMonitor()  # MAX30102 for heart rate
#     print("MAX30102 initialized successfully! ❤️")
#     hr_sensor.start_sensor()  # Start the heart rate sensor thread
#     time.sleep(5)  # Allow stabilization
#     at_least_one_sensor = True
# except Exception as e:
#     print(f"Failed to initialize MAX30102: {e}")
#     hr_sensor = None

# try:
#     i2c = board.I2C()  # Uses default I2C pins on Raspberry Pi (SDA: Pin 3, SCL: Pin 5)
#     temp_sensor = adafruit_pct2075.PCT2075(i2c)  # PCT2075 for temperature
#     print("PCT2075 initialized successfully! 🌡️")
#     at_least_one_sensor = True
# except Exception as e:
#     print(f"Failed to initialize PCT2075: {e}")
#     temp_sensor = None

# # Check if at least one sensor initialized successfully
# if not at_least_one_sensor:
#     print("No sensors initialized successfully. Exiting...")
#     exit()

# # SQLite setup for storing resting and current values
# def init_db():
#     conn = sqlite3.connect("health_data.db")
#     c = conn.cursor()
#     c.execute('''CREATE TABLE IF NOT EXISTS resting_values 
#                  (metric TEXT PRIMARY KEY, value REAL)''')
#     c.execute('''CREATE TABLE IF NOT EXISTS current_values 
#                  (timestamp TEXT, metric TEXT, value REAL, context TEXT)''')
#     conn.commit()
#     conn.close()

# # Store initial resting values (taken as an average over 10 seconds at rest)
# def store_resting_values():
#     conn = sqlite3.connect("health_data.db")
#     c = conn.cursor()
    
#     # Collect resting values over 10 seconds
#     hr_samples = []
#     temp_samples = []
#     accel_samples = {"x": [], "y": [], "z": []}
#     print("Collecting resting values for 10 seconds... Please remain still.")
#     for _ in range(10):
#         # Heart Rate
#         if hr_sensor:
#             bpm = hr_sensor.bpm
#             if bpm > 0:
#                 hr_samples.append(bpm)
        
#         # Temperature (PCT2075)
#         if temp_sensor:
#             temp = temp_sensor.temperature
#             temp_samples.append(temp)
        
#         # Accelerometer
#         if accel_sensor:
#             accel_data = accel_sensor.get_accel_data()
#             accel_samples["x"].append(accel_data["x"])
#             accel_samples["y"].append(accel_data["y"])
#             accel_samples["z"].append(accel_data["z"])
        
#         time.sleep(1)
    
#     # Calculate averages with fallbacks
#     resting_data = {
#         "Heart_Rate": sum(hr_samples) / len(hr_samples) if hr_samples else 70.0,
#         "Body_Temperature": sum(temp_samples) / len(temp_samples) if temp_samples else 25.0,
#         "Accel_X": sum(accel_samples["x"]) / len(accel_samples["x"]) if accel_samples["x"] else 0.0,
#         "Accel_Y": sum(accel_samples["y"]) / len(accel_samples["y"]) if accel_samples["y"] else 0.0,
#         "Accel_Z": sum(accel_samples["z"]) / len(accel_samples["z"]) if accel_samples["z"] else 0.0,
#     }
    
#     # Store in database
#     for metric, value in resting_data.items():
#         c.execute("INSERT OR REPLACE INTO resting_values (metric, value) VALUES (?, ?)", (metric, value))
#     conn.commit()
#     conn.close()
#     print("Resting values stored:", resting_data)

# def collect_sensor_data(context="resting"):
#     # Collect live sensor data with fallbacks
#     bpm = hr_sensor.bpm if hr_sensor and hr_sensor.bpm > 0 else 70.0  # Fallback if no valid reading
#     temp = temp_sensor.temperature if temp_sensor else 25.0  # Fallback if no temp sensor
#     accel_data = accel_sensor.get_accel_data() if accel_sensor else {"x": 0.0, "y": 0.0, "z": 0.0}  # Fallback if no accel sensor
    
#     return {
#         "Heart_Rate": bpm,
#         "Body_Temperature": temp,
#         "Accel_X": accel_data["x"],
#         "Accel_Y": accel_data["y"],
#         "Accel_Z": accel_data["z"],
#         "timestamp": datetime.now().isoformat(),
#         "context": context
#     }

# def store_current_values(data):
#     conn = sqlite3.connect("health_data.db")
#     c = conn.cursor()
#     timestamp = data["timestamp"]
#     context = data["context"]
#     for metric, value in data.items():
#         if metric not in ["timestamp", "context"]:
#             c.execute("INSERT INTO current_values (timestamp, metric, value, context) VALUES (?, ?, ?, ?)", 
#                       (timestamp, metric, value, context))
#     conn.commit()
#     conn.close()

# def on_connect(client, userdata, flags, rc):
#     if rc == 0:
#         print("Successfully connected to broker")
#     else:
#         print(f"Connection failed with code {rc}")

# # Initialize database and resting values
# init_db()
# store_resting_values()

# # Create publisher client
# publisher = mqtt.Client()
# publisher.on_connect = on_connect
# publisher.connect("broker.hivemq.com", 1883, 60)
# publisher.loop_start()

# try:
#     contexts = ["resting", "running", "walking", "exercising"]
#     current_context_index = 0
    
#     while True:
#         if random.randint(1, 5) == 1:
#             current_context_index = (current_context_index + 1) % len(contexts)
        
#         context = contexts[current_context_index]
#         sensor_data = collect_sensor_data(context)
#         store_current_values(sensor_data)
        
#         topic = "health_sensor/data"
#         publisher.publish(topic, json.dumps(sensor_data), qos=1)
#         print(f"Published to {topic} (Context: {context}): {sensor_data}")
#         time.sleep(1)

# except KeyboardInterrupt:
#     print("Stopping publisher... User can now request insights.")
#     if hr_sensor:
#         hr_sensor.stop_sensor()
#     publisher.loop_stop()
#     publisher.disconnect()