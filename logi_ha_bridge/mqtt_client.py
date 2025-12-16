import json
from typing import TYPE_CHECKING

import paho.mqtt.client as mqtt
from config import Config

if TYPE_CHECKING:
    from button import LogiButton


class MqttClient:
    def __init__(self, config: Config):
        self.config = config

        print("Setting up MQTT client...")
        self.client = mqtt.Client()
        self.client.username_pw_set(config.mqtt.username, config.mqtt.password)
        self.client.on_connect = self.on_connect
        print("MQTT client set up.")

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
            # Once connected, publish the discovery configuration.
            # self.publish_ha_discovery_config(client)
        else:
            print(f"Failed to connect to MQTT Broker, return code {rc}\n")

    def publish_ha_discovery_config(client, logi_button: "LogiButton"):
        """
        Publishes the configuration payload to Home Assistant's discovery topic.
        This makes the button appear as a device with a trigger.
        """
        discovery_payload = {
            "automation_type": "trigger",
            "topic": logi_button.action_topic,
            "type": "button_short_press",  # We can use any of HA's built-in types
            "subtype": "button_1",
            "payload": "press",  # The message we'll send on the action topic
            "device": {
                "identifiers": [logi_button.device_id],
                "name": logi_button.device_name,
                "manufacturer": "Logitech (via Python Bridge)",
            },
        }
        # Convert dict to JSON string and publish
        payload_str = json.dumps(discovery_payload)
        print(f"Publishing MQTT Discovery config to: {logi_button.config_topic}")
        client.publish(
            logi_button.config_topic, payload_str, retain=True
        )  # Retain ensures HA sees it after a restart
