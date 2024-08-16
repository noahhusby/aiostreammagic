import asyncio
import os
import sys
from asyncio import AbstractEventLoop


sys.path.insert(1, os.path.join(os.path.dirname(__file__), ".."))
from aiostreammagic import StreamMagicClient

async def demo(loop: AbstractEventLoop, host: str):
    cambridge = StreamMagicClient(host)
    print('1')
    await cambridge.power_on()
    await asyncio.sleep(2)
    info = await cambridge.get_state()
    print(info.to_json())
    await asyncio.sleep(1)
    x = await cambridge.get_sources()
    print(x)
    await asyncio.sleep(5)
    await cambridge.set_source_by_id('SPOTIFY')

    while True:
        await asyncio.sleep(1)


loop = asyncio.get_event_loop()
loop.set_debug(True)
loop.run_until_complete(demo(loop, sys.argv[1]))
loop.close()