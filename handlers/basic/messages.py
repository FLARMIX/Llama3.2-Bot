import asyncio
from datetime import datetime, timedelta

from PIL import Image
from aiogram import Router, F, Bot
from aiogram.enums import ChatAction
from aiogram.types import Message, PhotoSize, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton
import logging
import os

from API.OllamaAPI import OllamaAPI
from Database.Database import Database

router = Router()
ollama = OllamaAPI()
db = Database()
logger = logging.getLogger(__name__)

# Клавиатура для очистки чата
clear_chat_button = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🗑 Очистить чат")]],
    resize_keyboard=True,
    one_time_keyboard=False
)


async def show_typing_status(chat_id: int, bot: Bot):
    while True:
        await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        await asyncio.sleep(3)


# Функция для сборки контекста чата
async def build_chat_context(user_id: int) -> list:
    """Forms the history of chat for transfer to the neural network."""
    history = await db.get_recent_chat_history(user_id, limit=25)

    # Добавляем только одно system-сообщение
    messages = [{"role": "system", "content": "You are telegram bot based on AI Gemma3. Bot created by @FLARMIX."
                                              "Do not use any LaTeX, HTML, or Markdown formatting in your answers. "
                                              "Always reply in plain text. Avoid symbols like ^, _, $, <, >,"
                                              " and do not use tags such as <sup>, <sub>, or equations."}]

    for msg in history:
        messages.append({"role": "user", "content": msg["user_content"]})
        messages.append({"role": "assistant", "content": msg["ai_content"]})

    return messages


# Processing of a text request
@router.message(F.text & ~F.text.startswith('/') & ~F.text.in_(
    ["🗑 Очистить чат", "меню", "Меню", "Помощь", "помощь", "Настройки", "настройки"]))
async def handle_message(message: Message):
    # Проверяем, является ли чат группой/супергруппой
    if message.chat.type in ["group", "supergroup"]:
        flag = True
        # Для групповых чатов проверяем наличие prompt в начале сообщения
        if not message.text.lower().startswith("prompt"):
            return  # Игнорируем сообщение без prompt
    else:
        flag = False

    user_id = message.from_user.id

    user_stats = await db.get_user_stats(user_id)
    current_tokens = user_stats.get("current_tokens", 0)
    max_tokens = user_stats.get("max_tokens")  # Максимальный лимит токенов
    last_tokens_got = user_stats.get("last_tokens_got", None)

    now = datetime.now()

    # Проверяем, прошло ли 24 часа с последнего пополнения
    if last_tokens_got:
        last_tokens_got = datetime.strptime(last_tokens_got, "%Y-%m-%d %H:%M:%S")
    else:
        last_tokens_got = now - timedelta(days=1)  # Если NULL, значит первый раз

    if now - last_tokens_got >= timedelta(days=1):
        # Если баланс выше лимита, не пополняем
        if current_tokens < max_tokens:
            current_tokens += max_tokens - current_tokens  # Количество ежедневных запросов
            await db.update_user_stat("current_tokens", current_tokens, user_id)

        # Обновляем дату последнего пополнения
        await db.update_user_stat("last_tokens_got", now.strftime("%Y-%m-%d %H:%M:%S"), user_id)

    if current_tokens < 1:
        # Если в базе last_tokens_got почему-то хранится строкой, конвертируем
        if isinstance(last_tokens_got, str):
            last_tokens_got = datetime.strptime(last_tokens_got, "%Y-%m-%d %H:%M:%S")

        # Рассчитываем следующее начисление (24 часа после последнего)
        next_refill_time = last_tokens_got + timedelta(hours=24)

        # Получаем текущее время
        now = datetime.now()

        # Вычисляем оставшееся время до пополнения
        time_left = next_refill_time - now  # Это уже timedelta
        hours, remainder = divmod(time_left.total_seconds(), 3600)
        minutes = remainder // 60

        await message.reply(
            f"У вас закончились токены! Приходите через {int(hours)} ч. {int(minutes)} мин. или пополните баланс.")
        return

    typing_action = asyncio.create_task(show_typing_status(message.chat.id, message.bot))
    await db.create_user(user_id)

    try:
        prompt = message.text
        if flag:
            prompt = prompt[len("prompt")::]

        chat_context = await build_chat_context(user_id)  # Get chat history

        response_data, tokens = await ollama.generate_response(chat_history=chat_context, user_prompt=prompt,
                                                               max_tokens=800)

        # Извлекаем только контент из ответа (ответ от AI)
        ai_content = response_data.get("content", "")

        if not ai_content:
            await message.reply("🤖 Модель не смогла сгенерировать ответ.")
            return

        # Обновляем токены
        current_tokens = await db.get_user_stats(user_id)
        current_tokens = current_tokens.get("current_tokens")
        print(current_tokens)
        await db.update_user_stat("current_tokens", current_tokens - 1, user_id)

        # Сохраняем сообщение в базе данных
        await db.save_message(user_id, prompt, ai_content)

        # Отправляем ответ пользователю
        await message.reply(ai_content, reply_markup=clear_chat_button, parse_mode=None)

    except Exception as e:
        logger.error(f"Ошибка: {str(e)}", exc_info=True)
        await message.reply("⚠️ Произошла внутренняя ошибка.")
    finally:
        typing_action.cancel()


# Image processing
@router.message(F.photo)
async def handle_photo(message: Message):
    # Проверяем, является ли чат группой/супергруппой
    if message.chat.type in ["group", "supergroup"]:
        flag = True
        # Для групповых чатов проверяем наличие prompt в начале
        if not message.text.lower().startswith("prompt"):
            return  # Игнорируем сообщение без prompt
    else:
        flag = False

    typing_action = asyncio.create_task(show_typing_status(message.chat.id, message.bot))
    user_id = message.from_user.id
    if not await db.check_user_exists(user_id):
        await db.create_user(user_id)

    try:
        photo: PhotoSize = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)

        # Load the image in memory (without storing to disk)
        await message.bot.download_file(file.file_path, "temp_files/temp_picture.jpg")

        # Reduce the image for transmission to the neural network
        with Image.open("temp_files/temp_picture.jpg") as img:
            original_width, original_height = img.width, img.height

            changed_size = (original_width // 2, original_height // 2)

            resized_img = img.resize(changed_size)
            resized_img.save("temp_files/changed_temp_picture.jpg")

        base64_image = await ollama.encode_image_to_base64("temp_files/changed_temp_picture.jpg")

        # Get a text description (if any)
        user_caption = message.caption if message.caption else "Что изображено на картинке?"
        if flag:
            user_caption = user_caption[len("prompt"):].strip()

        # Load the history of the chat
        chat_context = await build_chat_context(user_id)

        response, tokens = await ollama.generate_response(chat_history=chat_context, user_prompt=user_caption,
                                                          images=[base64_image], max_tokens=800)

        if not response.get('content'):
            await message.reply("🤖 Модель не смогла сгенерировать ответ.")
            return

        current_tokens = await db.get_user_stats(user_id)
        current_tokens = current_tokens.get("current_tokens")
        await db.update_user_stat("current_tokens", current_tokens - 1, user_id)
        await db.save_message(user_id, f"{user_caption}", response.get('content'))
        await message.reply(response.get('content'), reply_markup=clear_chat_button, parse_mode=None)

    except Exception as e:
        logger.error(f"Ошибка обработки изображения: {str(e)}", exc_info=True)
        await message.reply("⚠️ Произошла ошибка при обработке изображения.")
    finally:
        typing_action.cancel()
        # Delete temporary files
        os.remove("temp_files/temp_picture.jpg")
        os.remove("temp_files/changed_temp_picture.jpg")


# Chat cleanup
@router.message(F.text == "🗑 Очистить чат")
async def clear_chat(message: Message):
    user_id = message.from_user.id
    await db.delete_chat_history(user_id)
    await message.reply("✅ История сообщений удалена.", reply_markup=clear_chat_button)
    return  # Stop the processing further!


# Help message
@router.message(F.text.in_(["помощь", "Помощь"]))
async def help_button(message: Message):
    typing_action = asyncio.create_task(show_typing_status(message.chat.id, message.bot))
    messages = [{"role": "system", "content": "You are telegram bot based on AI Gemma3. Bot created by @FLARMIX. "
                                              "You can processing pictures."
                                              "Please avoid using any HTML tags in your responses. Provide plain text "
                                              "only."}]

    response = await ollama.generate_response(chat_history=messages,
                                              user_prompt="Расскажи о себе. Что ты можешь, кто ты. "
                                                          "Расскажи так чтобы я читал не много, "
                                                          "но сразу понял всё о тебе. "
                                                          "В конце пожелай приятного пользования ботом.",
                                              max_tokens=300)

    await message.reply(response[0].get('content'))
    typing_action.cancel()
    return  # Stop the processing further!
