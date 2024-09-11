import asyncio

from aiostreammagic import StreamMagicClient

HOST = "192.168.20.218"


async def on_state_change(client: StreamMagicClient):
    """Called when new information is received."""
    print(f"System info: {client.get_info()}")
    print(f"Sources: {client.get_sources()}")
    print(f"State: {client.get_state()}")
    print(f"Play State: {client.get_play_state()}")
    print(f"Now Playing: {client.get_now_playing()}")

async def main():
    """Subscribe demo entrypoint."""
    client = StreamMagicClient("192.168.20.218")
    await client.register_state_update_callbacks(on_state_change)
    await client.connect()

    # Play media using the unit's front controls or StreamMagic app
    await asyncio.sleep(60)

    await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
