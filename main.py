import asyncio
import logging

from app import App
from app.logger import LoggerFormat

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
fh = logging.FileHandler('test.log', 'w+')
fh.setLevel(logging.INFO)
formatter = LoggerFormat(fmt='[%(levelname)s] [%(threadName)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.addHandler(fh)


async def main():
    future = asyncio.Future()
    app = App()
    app.start()
    await future


if __name__ == '__main__':
    asyncio.run(main())
