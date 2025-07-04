import asyncio
import logging
from loader import main_run
from Database.Database import Database


async def main():
    # Инициализация базы данных
    db = Database()
    await db.init_db()

    # Запуск бота
    await main_run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())