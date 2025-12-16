import paho.mqtt.client as mqtt
from config import Config


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
        else:
            print(f"Failed to connect to MQTT Broker, return code {rc}\n")
