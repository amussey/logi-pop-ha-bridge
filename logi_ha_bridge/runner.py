import asyncio

from listener import LogiHaBridgeListener


async def main():
    bridge = LogiHaBridgeListener()
    await bridge.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program stopped.")
