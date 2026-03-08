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
#
# This cooldown is also applied when a press event is received via MQTT from
# another bridge instance, ensuring that only one instance publishes per
# physical press (cross-instance deduplication).
BUTTON_COOLDOWN = 3.0


class LogiHaBridgeListener:
    """
    Listens for Logi POP button BLE advertisements using a persistent scanner
    and handles multiple buttons concurrently.

    Detection is purely advertisement-based - no GATT connections are made.
    The buttons only advertise when pressed, so detecting an advertisement IS
    the press event.  This keeps the BLE adapter free at all times, ensuring
    that buttons pressed within seconds of each other are always caught.

    Cross-instance deduplication:
      Each instance subscribes to the MQTT action topics for all Logi POP
      buttons.  When any instance publishes a press event, all instances
      (including itself) receive it and enter cooldown for that button.
      If two instances detect the same BLE advertisement, the first one to
      publish wins; the others see the MQTT message and suppress their own
      publish because the button is already in cooldown.
    """

    def __init__(self):
        print("Initializing Logi HA Bridge...")
        self.config = Config.load()
        self.mqtt_client = MqttClient(self.config)
        self.buttons: dict[str, LogiButton] = {}
        self.cooldowns: dict[str, float] = {}

        # Maps device_id -> BLE address for reverse lookup from MQTT messages.
        self._device_id_to_addr: dict[str, str] = {}

        # Register MQTT callback for cross-instance dedup.
        self.mqtt_client.set_on_logi_press(self._on_mqtt_press_received)

    def _on_mqtt_press_received(self, device_id: str):
        """Called when a press event is received via MQTT (from any instance).

        Enters cooldown for the corresponding button so this instance does
        not publish a duplicate if it also saw the same BLE advertisement.
        """
        # Reverse-lookup: find the BLE address for this device_id.
        addr = self._device_id_to_addr.get(device_id)
        if addr is None:
            # We haven't seen this button via BLE yet.  Derive the address
            # from the device_id format: logi_pop_switch_<addr_hex>
            # e.g. logi_pop_switch_cc78aba88dba -> CC:78:AB:A8:8D:BA
            hex_part = device_id.replace("logi_pop_switch_", "")
            if len(hex_part) == 12:
                addr = ":".join(
                    hex_part[i : i + 2].upper() for i in range(0, 12, 2)  # noqa: E203
                )
            else:
                return  # Unrecognised device_id format

        now = time.monotonic()
        # Only set cooldown if not already in one -- don't extend it.
        if addr not in self.cooldowns or now >= self.cooldowns[addr]:
            self.cooldowns[addr] = now + BUTTON_COOLDOWN

    def _on_device_detected(self, device, advertisement_data):
        """Called by BleakScanner for every BLE advertisement received."""
        if not LogiButton.is_logi_button(device, advertisement_data):
            return

        addr = device.address
        now = time.monotonic()

        # Skip if still in cooldown from a local detection or a press
        # published by another instance (cross-instance dedup).
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

        # Cache the device_id -> address mapping for MQTT reverse lookup.
        self._device_id_to_addr[button.device_id] = addr

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
