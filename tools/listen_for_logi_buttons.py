import asyncio

from bleak import BleakScanner

# Set to store addresses of devices we've already printed
found_devices = set()
LOGI_DEVICE_NAME = "logi switch"


def detection_callback(device, advertisement_data):
    """
    Callback function that is called when a device is discovered or
    advertising data is received.
    """
    # Get the device name. Prefer the name in the advertisement data (local_name),
    # falling back to the cached device.name, or Unknown.
    device_name = advertisement_data.local_name or device.name or "Unknown"

    if LOGI_DEVICE_NAME in device_name.lower():

        # Check if we have already printed this device
        if device.address not in found_devices:
            print("\n[FOUND] match for 'logi':")
            print(f"  Name:    {device_name}")
            print(f"  Address: {device.address}")
            print(f"  RSSI:    {advertisement_data.rssi} dBm")

            # Add to the set so we don't print it again
            found_devices.add(device.address)


async def main():
    print("Scanning for devices with 'logi' in the name...")
    print("Press Ctrl+C to stop.")

    # create the scanner with our callback
    scanner = BleakScanner(detection_callback=detection_callback)

    # Start the scanner
    await scanner.start()

    try:
        # Keep the script running indefinitely to listen for advertisements
        # We use a simple sleep loop here to keep the event loop active
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("\nScanning stopped.")
    finally:
        # Ensure we stop the scanner when the script exits
        await scanner.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nUser interrupted script.")
