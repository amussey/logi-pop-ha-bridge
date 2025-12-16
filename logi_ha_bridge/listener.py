import asyncio

from bleak import BleakError, BleakScanner
from button import LogiButton
from config import Config
from mqtt_client import MqttClient


class LogiHaBridgeListener:
    """Interface for BLE event listeners."""

    def __init__(self):
        print("Initializing Logi HA Bridge...")
        self.config = Config.load()
        self.mqtt_client = MqttClient(self.config)

    async def run(self):
        """The main function that starts the BLE scanner."""
        print("=" * 80)
        print("Starting Logi HA Bridge!")
        print("-" * 80)

        self.mqtt_client.start()

        print("Starting Logi Switch listener...")
        try:
            while True:
                try:
                    device = await BleakScanner.find_device_by_filter(
                        LogiButton.is_logi_button, timeout=5.0
                    )
                    if device:
                        logi_button = LogiButton(device, self.mqtt_client)
                        await logi_button.listen()
                except BleakError as e:
                    print("BLE Error during scanning:", e)
                    await asyncio.sleep(2)
                    continue
        except KeyboardInterrupt:
            print("\nStopping scanner...")
            # await scanner.stop()
            self.mqtt_client.stop()
