import asyncio

from aiostreammagic import StreamMagicClient, Source, Info

HOST = "192.168.x.x"  # Replace with your StreamMagic device's IP address


async def main() -> None:
    """Basic demo entrypoint."""
    client = StreamMagicClient(HOST)
    await client.connect()

    info: Info = await client.get_info()
    sources: list[Source] = await client.get_sources()

    print(f"Model: {info.model}")
    for source in sources:
        print(f"Name: {source.id} ({source.id})")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
