import asyncio

from bleak import AdvertisementData, BleakScanner, BLEDevice
from button import LogiButton
from config import Config
from inventory import LogiButtonInventory
from mqtt_client import MqttClient


class LogiHaBridgeListener:
    """Interface for BLE event listeners."""

    def __init__(self):
        print("Initializing Logi HA Bridge...")
        self.config = Config.load()
        self.logi_button_inventory = LogiButtonInventory()
        self.mqtt_client = MqttClient(self.config)

    async def run(self):
        """The main function that starts the BLE scanner."""
        print("=" * 80)
        print("Starting Logi HA Bridge!")
        print("-" * 80)

        self.mqtt_client.start()

        print("Starting Logi Switch listener...")
        scanner = BleakScanner(detection_callback=self.on_advertisement)
        await scanner.start()

        try:
            while True:
                await asyncio.sleep(5)
        except KeyboardInterrupt:
            print("\nStopping scanner...")
            await scanner.stop()
            self.mqtt_client.stop()

    def on_advertisement(
        self, device: BLEDevice, advertisement_data: AdvertisementData
    ):
        """
        Listens for a new event from the switch and publishes an MQTT message.
        """
        if LogiButton.is_logi_button(device, advertisement_data):
            self.logi_button_inventory.process_event(device, advertisement_data)

            # mqtt_client.publish(ACTION_TOPIC, "press")
