import paho.mqtt.client as mqtt
from config import Config

# Wildcard topic to subscribe to all Logi POP button action events.
# Used for cross-instance deduplication: each bridge instance sees press
# events published by other instances and enters cooldown to avoid
# publishing a duplicate.
LOGI_ACTION_TOPIC_WILDCARD = "homeassistant/device_automation/logi_pop_switch_+/action"


class MqttClient:
    def __init__(self, config: Config):
        self.config = config
        self._on_logi_press_callback = None

        print("Setting up MQTT client...")
        self.client = mqtt.Client()
        self.client.username_pw_set(config.mqtt.username, config.mqtt.password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self._on_message
        print("MQTT client set up.")

    def set_on_logi_press(self, callback):
        """Register a callback for when a Logi button press is received via MQTT.

        The callback signature is: callback(device_id: str)
        where device_id is extracted from the topic, e.g. 'logi_pop_switch_cc78aba88dba'.
        """
        self._on_logi_press_callback = callback

    def start(self):
        self.client.connect(self.config.mqtt.broker_address, self.config.mqtt.port, 60)
        self.client.loop_start()  # Start MQTT client in the background

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the MQTT broker."""
        if rc == 0:
            print("Connected to MQTT Broker successfully!")
            # Subscribe to all Logi button action topics for cross-instance dedup.
            client.subscribe(LOGI_ACTION_TOPIC_WILDCARD)
            print(f"Subscribed to {LOGI_ACTION_TOPIC_WILDCARD}")
        else:
            print(f"Failed to connect to MQTT Broker, return code {rc}\n")

    def _on_message(self, client, userdata, msg):
        """Callback for incoming MQTT messages."""
        # Extract device_id from topic:
        # homeassistant/device_automation/<device_id>/action
        parts = msg.topic.split("/")
        if len(parts) >= 3 and self._on_logi_press_callback:
            device_id = parts[2]
            self._on_logi_press_callback(device_id)
