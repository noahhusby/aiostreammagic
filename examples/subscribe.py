import asyncio

from aiostreammagic import StreamMagicClient
from aiostreammagic.models import CallbackType

HOST = "192.168.20.218"


async def on_state_change(client: StreamMagicClient, callback_type: CallbackType):
    """Called when new information is received."""
    print(f"Callback Type: {callback_type} {client.is_connected()}")
    print(f"System info: {client.info}")
    print(f"Sources: {client.sources}")
    print(f"State: {client.state}")
    print(f"Play State: {client.play_state}")
    print(f"Now Playing: {client.now_playing}")


async def main():
    """Subscribe demo entrypoint."""
    client = StreamMagicClient("192.168.20.218")
    await client.register_state_update_callbacks(on_state_change)
    await client.connect()

    # Play media using the unit's front controls or StreamMagic app
    await asyncio.sleep(60)

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
