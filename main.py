import asyncio
import logging
from loader import main_run

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main_run())
