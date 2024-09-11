import asyncio

from aiostreammagic import StreamMagicClient, Source, Info

HOST = "192.168.20.218"


async def main():
    """Basic demo entrypoint."""
    client = StreamMagicClient("192.168.20.218")
    await client.connect()

    info: Info = await client.get_info()
    sources: list[Source] = await client.get_sources()

    print(f"Model: {info.model}")
    for source in sources:
        print(f"Name: {source.id} ({source.id})")

    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
