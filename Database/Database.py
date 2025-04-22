import json
from typing import List, Any

import aiosqlite
import config


class Database:
    def __init__(self, db_path="main.db"):
        self.db_path = db_path

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    current_tokens INTEGER NOT NULL,
                    max_tokens INTEGER NOT NULL,
                    bot_options DICTIONARY NOT NULL,
                    is_admin BOOLEAN NOT NULL,
                    last_tokens_got DATE NOT NULL
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    user_content TEXT,
                    ai_content TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')

            await db.commit()

    async def create_user(self, user_id):
        if await self.check_user_exists(user_id):
            return

        async with aiosqlite.connect(self.db_path) as db:
            bot_options = json.dumps({
                "temperature": config.temperature,
                "repeat_penalty": config.repeat_penalty,
                "presence_penalty": config.presence_penalty,
                "frequency_penalty": config.frequency_penalty,
                "top_p": config.top_p
            })

            await db.execute('INSERT INTO users (user_id, current_tokens, max_tokens, bot_options, is_admin, '
                             'last_tokens_got)'
                             ' VALUES (?, ?, ?, ?, ?, ?)', (user_id, 10, 10, bot_options, 0, "1970-01-01 "
                                                                                             "00:00:00"))
            await db.commit()

    async def check_user_exists(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM Users WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
            return row[0] > 0

    async def save_message(self, user_id: int, user_content: str, ai_content: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'INSERT INTO messages (user_id, user_content, ai_content) VALUES (?, ?, ?)',
                (user_id, user_content, ai_content)
            )
            await db.commit()

    async def make_admin(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('UPDATE users SET is_admin = 1 WHERE user_id = ?', (user_id,))
            await db.commit()

    # Get bot options from Database
    async def get_bot_options(self, user_id: int) -> dict:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT bot_options FROM users WHERE user_id = ?', (user_id,))
            row = await cursor.fetchone()
            return json.loads(row[0]) if row else None

    async def get_user_stats(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT current_tokens, max_tokens, last_tokens_got FROM users WHERE user_id = ?', (user_id,))
            row = await cursor.fetchone()
            if row:
                return {
                    "current_tokens": row[0],
                    "max_tokens": row[1],
                    "last_tokens_got": row[2]
                }
            else:
                return None

    async def update_bot_option(self, option: str, new_value: Any, user_id: int) -> None:
        bot_options = await self.get_bot_options(user_id)  # Получаем текущие настройки
        if option in bot_options:  # Проверяем, существует ли такой параметр
            bot_options[option] = new_value  # Обновляем значение

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "UPDATE users SET bot_options = ? WHERE user_id = ?",
                    (json.dumps(bot_options), user_id)  # Сохраняем JSON обратно
                )
                await db.commit()  # Фиксируем изменения

    async def update_user_stat(self, stat: str, new_value: Any, user_id: int) -> None:
        user_stats = await self.get_user_stats(user_id)  # Получаем текущие данные
        print(user_stats)
        if stat in user_stats:  # Проверяем, есть ли нужное поле
            print(stat)
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(f"UPDATE users SET {stat} = ? WHERE user_id = ?", (new_value, user_id))
                await db.commit()

    async def get_recent_chat_history(self, user_id: int, limit: int = 50) -> List[dict]:
        """Returns the latter N User messages (to transfer the context to the neural network)."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                'SELECT user_content, ai_content FROM messages WHERE user_id = ? ORDER BY message_id DESC LIMIT ?',
                (user_id, limit)
            )
            rows = await cursor.fetchall()
            return [{"user_content": row[0], "ai_content": row[1]} for row in reversed(rows)]  # Восстанавливаем порядок

    async def delete_chat_history(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('DELETE FROM messages WHERE user_id = ?', (user_id,))
            await db.commit()
