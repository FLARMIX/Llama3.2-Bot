from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

import config
from handlers.init_router import router


async def main_run() -> None:
    """
    This function initializes and runs the bot using aiogram.

    The function performs the following steps:
    1. Creates an instance of the Bot class with the provided bot token and default bot properties.
    2. Creates an instance of the Dispatcher class with a MemoryStorage storage.
    3. Includes the router from the handlers.init_router module in the dispatcher.
    4. Assigns the bot instance to the dispatcher's "bot" key.
    5. Deletes any existing webhook and starts polling for updates.

    Parameters:
    None

    Returns:
    None
    """
    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    dp["bot"] = bot

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
