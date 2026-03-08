import asyncio
import time

from bleak import BleakScanner
from button import LogiButton
from config import Config
from mqtt_client import MqttClient

# Cooldown after handling a button before accepting it again (seconds).
# Prevents duplicate triggers from repeated BLE advertisements for the same
# physical press.  Tuned via empirical testing: buttons re-advertise for ~1-2s
# after a press, so 3s reliably deduplicates while still catching presses
# spaced 4+ seconds apart on the same button.
BUTTON_COOLDOWN = 3.0


class LogiHaBridgeListener:
    """
    Listens for Logi POP button BLE advertisements using a persistent scanner
    and handles multiple buttons concurrently.

    Detection is purely advertisement-based - no GATT connections are made.
    The buttons only advertise when pressed, so detecting an advertisement IS
    the press event.  This keeps the BLE adapter free at all times, ensuring
    that buttons pressed within seconds of each other are always caught.
    """

    def __init__(self):
        print("Initializing Logi HA Bridge...")
        self.config = Config.load()
        self.mqtt_client = MqttClient(self.config)
        self.buttons: dict[str, LogiButton] = {}
        self.cooldowns: dict[str, float] = {}

    def _on_device_detected(self, device, advertisement_data):
        """Called by BleakScanner for every BLE advertisement received."""
        if not LogiButton.is_logi_button(device, advertisement_data):
            return

        addr = device.address
        now = time.monotonic()

        # Skip if still in cooldown from a recent interaction.
        if addr in self.cooldowns and now < self.cooldowns[addr]:
            return

        # Start cooldown immediately so later advertisements for the same
        # physical press are ignored.
        self.cooldowns[addr] = now + BUTTON_COOLDOWN

        # Create button object on first discovery; reuse on subsequent ones.
        if addr not in self.buttons:
            self.buttons[addr] = LogiButton(device, self.mqtt_client)
        else:
            # Update the underlying device reference (may carry fresher info).
            self.buttons[addr].device = device

        button = self.buttons[addr]
        print(f"\n>>> Button press detected: {addr}")
        button._trigger_press("Press")

    async def run(self):
        """Start the persistent BLE scanner and dispatch button events."""
        print("=" * 80)
        print("Starting Logi HA Bridge!")
        print("-" * 80)

        self.mqtt_client.start()

        print("Starting continuous BLE scanner...")
        scanner = BleakScanner(detection_callback=self._on_device_detected)

        try:
            await scanner.start()
            print("Scanner running. Waiting for button presses...")
            print("=" * 80)

            while True:
                await asyncio.sleep(0.5)

        except (KeyboardInterrupt, asyncio.CancelledError):
            print("\nStopping...")
        finally:
            await scanner.stop()
            self.mqtt_client.stop()
            print("Logi HA Bridge stopped.")
