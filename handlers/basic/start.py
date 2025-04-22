from aiogram import Router, types
from aiogram.filters import Command

import config
from Database.Database import Database
from config import MODEL

router = Router()
db = Database()
ADMINS = config.ADMIN_IDs
print(ADMINS)


@router.message(Command("start"))
async def cmd_start(message: types.Message) -> None:
    """
    This function handles the '/start' command. It checks if the user exists in the database,
    creates a new user if necessary, and assigns admin privileges if the user's ID is in the ADMINS list.
    It then sends a welcome message to the user.

    Parameters:
    message (types.Message): The incoming message object from the Telegram bot.

    Returns:
    None
    """
    user_id = message.from_user.id
    print(user_id)
    if not await db.check_user_exists(user_id):
        await db.create_user(user_id)
    if user_id in ADMINS:
        await db.update_user_stat("is_admin", 1, user_id)
        await db.update_user_stat("max_tokens", 1_000_000_000_000_000_000_000_000_000, user_id)
        await db.update_user_stat("current_tokens", 1_000_000_000_000_000_000_000_000_000, user_id)
        await message.answer('Вы администратор!')

    await message.answer(f'Это чатбот на базе ИИ {MODEL.capitalize()}. Для ознакомления напишите "Меню".'
                         '\nЛибо вы можете начать общаться прямо сейчас, просто написав сообщение!')
