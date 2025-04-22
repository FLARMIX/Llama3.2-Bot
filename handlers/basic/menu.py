from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

router = Router()


@router.message(Command("menu"))
@router.message(F.text.lower() == "меню")
async def show_menu(message: types.Message) -> None:
    """
        Display the main menu with predefined buttons.

        This function creates and sends a reply keyboard markup with buttons
        for "Settings" and "Help" when the user sends the command "/menu" or
        types "меню" (case-insensitive).

        Parameters:
        message (types.Message): The incoming message object from the user.

        Returns:
        None: This function doesn't return anything. It sends a message with
        a reply keyboard markup to the user.
    """
    builder = ReplyKeyboardBuilder()
    buttons = ["Настройки", "Помощь"]
    for btn in buttons:
        builder.add(types.KeyboardButton(text=btn))
    builder.adjust(2)
    await message.answer("📱 Главное меню:", reply_markup=builder.as_markup(resize_keyboard=True))
