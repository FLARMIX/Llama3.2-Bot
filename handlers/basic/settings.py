from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.fsm.state import State, StatesGroup

from Database.Database import Database

db = Database()
router = Router()


class ChangeTemperatureValue(StatesGroup):
    entering_value = State()


class ChangeRepeatPenaltyValue(StatesGroup):
    entering_value = State()


class ChangePresencePenaltyValue(StatesGroup):
    entering_value = State()


class ChangeFrequencePenaltyValue(StatesGroup):
    entering_value = State()


class ChangeTopKValue(StatesGroup):
    entering_value = State()


class ChangeTopPValue(StatesGroup):
    entering_value = State()


# Settings menu
@router.message(F.text.in_(["Настройки", "настройки"]))
async def settings_button(message: Message):
    user_id = message.from_user.id
    user_stats = await db.get_user_stats(user_id)
    current_tokens = user_stats.get("current_tokens")
    max_tokens = user_stats.get("max_tokens")

    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                      [InlineKeyboardButton(text="Изменить Temperature", callback_data="change_temperature")],
                      [InlineKeyboardButton(text="Изменить Repeat Penalty", callback_data="change_repeat_penalty")],
                      [InlineKeyboardButton(text="Изменить Presence Penalty", callback_data="change_presence_penalty")],
                      [InlineKeyboardButton(text="Изменить Frequency Penalty", callback_data="change_frequency_penalty")],
                      [InlineKeyboardButton(text="Изменить Top K", callback_data="change_top_k")],
                      [InlineKeyboardButton(text="Изменить Top P", callback_data="change_top_p")]
                                                            ])

    await message.answer(f"Ваши токены: {current_tokens}\nМакс. токенов: {max_tokens}"
                         f"\nНастройки бота (Для опытных пользователей!):", reply_markup=inline_keyboard)


# Temperature change
@router.callback_query(F.data == "change_temperature")
async def change_temperature(callback: CallbackQuery, state: FSMContext):
    user_id = callback.message.from_user.id
    bot_settings = await db.get_bot_options(user_id)
    temperature = bot_settings.get("temperature")
    await callback.message.answer(f"Текущая температура: {temperature}\nПо умолчанию 0.7\nВведите новую температуру:")
    await state.set_state(ChangeTemperatureValue.entering_value)


@router.callback_query(F.data == "change_repeat_penalty")
async def change_repeat_penalty(callback: CallbackQuery, state: FSMContext):
    user_id = callback.message.from_user.id
    bot_settings = await db.get_bot_options(user_id)
    repeat_penalty = bot_settings.get("repeat_penalty")
    await callback.message.answer(f"Текущий штраф за повторное сообщение: {repeat_penalty}"
                                  f"\nПо умолчанию 1.0\nВведите новый штраф за повторное сообщение (от 0.1 до 2.0):")
    await state.set_state(ChangeRepeatPenaltyValue.entering_value)


@router.message(ChangeRepeatPenaltyValue.entering_value)
async def changing_repeat_penalty(message: Message, state: FSMContext):
    user_id = message.from_user.id
    bot_settings = await db.get_bot_options(user_id)
    exist_values = range(1, 20)
    exist_values = [str(i / 10) for i in exist_values]
    if message.text not in exist_values:
        await message.answer(f"Введенное значение не является допустимым. "
                             f"Попробуйте еще раз. Со значениями от 0.1 до 2.0")
        return
    new_repeat_penalty = float(message.text)

    await db.update_bot_option("repeat_penalty", new_repeat_penalty, user_id)
    await message.answer("Штраф за повторное сообщение изменен успешно!")
    await state.clear()


@router.message(ChangeTemperatureValue.entering_value)
async def changing_temperature(message: Message, state: FSMContext):
    user_id = message.from_user.id
    bot_settings = await db.get_bot_options(user_id)
    exist_values = range(1, 10)
    exist_values = [str(i / 10) for i in exist_values]
    if message.text not in exist_values:
        await message.answer(f"Введенное значение не является допустимым. "
                             f"Попробуйте еще раз. Со значениями от 0.1 до 1.0")
        return

    new_temperature = float(message.text)

    await db.update_bot_option("temperature", new_temperature, user_id)
    await message.answer("Температура изменена успешно!")
    await state.clear()

