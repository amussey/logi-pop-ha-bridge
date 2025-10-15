# logi_ha_bridge.py

import asyncio
from bleak import BleakScanner
import paho.mqtt.client as mqtt
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()  # Loads variables from .env into os.environ

# --- CONFIGURATION ---
# -- Bluetooth Settings --
TRIGGER_DEVICE_ADDRESS = os.environ.get("TRIGGER_DEVICE_ADDRESS")
LOGITECH_MFG_ID = 257

# -- MQTT Settings --
MQTT_BROKER_ADDRESS = os.environ.get("MQTT_BROKER_ADDRESS")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))
MQTT_USERNAME = os.environ.get("MQTT_USERNAME")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD")

# --- Home Assistant MQTT Discovery Settings ---
# You can change these, but the defaults are good.
DEVICE_UNIQUE_ID = "logi_pop_switch_{}".format(TRIGGER_DEVICE_ADDRESS.replace(":", "").lower())
DEVICE_NAME = "Logi Pop Switch ({})".format(TRIGGER_DEVICE_ADDRESS.replace(":", "").lower())
# This is the topic Home Assistant will listen to for the button press.
ACTION_TOPIC = f"homeassistant/device_automation/{DEVICE_UNIQUE_ID}/action"
# This is the special topic for telling Home Assistant about our device.
CONFIG_TOPIC = f"homeassistant/device_automation/{DEVICE_UNIQUE_ID}/config"

# --- State Management ---
last_processed_counter = -1

def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the MQTT broker."""
    if rc == 0:
        print("Connected to MQTT Broker successfully!")
        # Once connected, publish the discovery configuration.
        publish_ha_discovery_config(client)
    else:
        print(f"Failed to connect to MQTT Broker, return code {rc}\n")

def publish_ha_discovery_config(client):
    """
    Publishes the configuration payload to Home Assistant's discovery topic.
    This makes the button appear as a device with a trigger.
    """
    discovery_payload = {
        "automation_type": "trigger",
        "topic": ACTION_TOPIC,
        "type": "button_short_press", # We can use any of HA's built-in types
        "subtype": "button_1",
        "payload": "press", # The message we'll send on the action topic
        "device": {
            "identifiers": [DEVICE_UNIQUE_ID],
            "name": DEVICE_NAME,
            "manufacturer": "Logitech (via Python Bridge)"
        }
    }
    # Convert dict to JSON string and publish
    payload_str = json.dumps(discovery_payload)
    print(f"Publishing MQTT Discovery config to: {CONFIG_TOPIC}")
    client.publish(CONFIG_TOPIC, payload_str, retain=True) # Retain ensures HA sees it after a restart

def on_advertisement(device, advertisement_data):
    """
    Listens for a new event from the switch and publishes an MQTT message.
    """
    global last_processed_counter

    if device.address == TRIGGER_DEVICE_ADDRESS and LOGITECH_MFG_ID in advertisement_data.manufacturer_data:
        data = advertisement_data.manufacturer_data[LOGITECH_MFG_ID]
        
        if len(data) >= 12:
            event_counter = data[11]
            
            # If this is a new event counter we haven't processed yet...
            if event_counter != last_processed_counter:
                last_processed_counter = event_counter
                
                print(f"\n--- BUTTON PRESS DETECTED (Counter: {event_counter}) ---")
                print(f"Sending 'press' message to MQTT topic: {ACTION_TOPIC}")
                
                # Publish the action message to the topic HA is listening on.
                mqtt_client.publish(ACTION_TOPIC, "press")

# --- Main Execution ---
# Set up MQTT client
print("Setting up MQTT client...")
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
mqtt_client.on_connect = on_connect
print("MQTT client set up.")

async def main():
    """The main function that starts the BLE scanner."""
    print("=" * 80)
    print("Starting Logi HA Bridge!")
    print("-" * 80)


    print("Attempting to connect to MQTT broker...")
    mqtt_client.connect(MQTT_BROKER_ADDRESS, MQTT_PORT, 60)
    mqtt_client.loop_start() # Start MQTT client in the background

    print("Starting Logi Switch listener...")
    scanner = BleakScanner(detection_callback=on_advertisement)
    await scanner.start()
    
    try:
        while True:
            await asyncio.sleep(5)
    except KeyboardInterrupt:
        print("\nStopping scanner...")
        await scanner.stop()
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program stopped.")