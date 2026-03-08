import asyncio
import signal

from listener import LogiHaBridgeListener


async def main():
    bridge = LogiHaBridgeListener()

    # Allow Ctrl-C to cancel the main task cleanly.
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: task.cancel())

    task = asyncio.ensure_future(bridge.run())
    try:
        await task
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program stopped.")
