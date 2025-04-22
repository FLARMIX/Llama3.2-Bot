import base64
from typing import Any

import aiohttp

import config


class OllamaAPI:
    def __init__(self):
        self.url = "http://localhost:11434/api"  # Local API for Ollama API
        self.model = f"{config.MODEL}"  # May be changed on another Multimodal Model like "Llama3.2-vision" in .env file
        # Not used code below
        self.default_properties = {
                "temperature": config.temperature,
                "repeat_penalty": config.repeat_penalty,
                "presence_penalty": config.presence_penalty,
                "frequency_penalty": config.frequency_penalty,
                "top_p": config.top_p
            }
        # Not used code is higher
        self.stream = False  # Do not change this variable!

    async def generate_response(self, chat_history: list, user_prompt: str, images: list | None = None,
                                max_tokens: int = 1000, options: dict[str: Any] | None = None) -> tuple[str, int]:
        """
            Generates a response based on the chat history, user prompt, and optional images.

            This asynchronous method sends a request to the Ollama API to generate a response
            based on the provided chat history and user prompt. It can also process images
            if provided.

            Parameters:
            chat_history (list): A list of previous chat messages, each as a dictionary
                                 with 'role' and 'content' keys.
            user_prompt (str): The current user's input or question.
            images (list | None): Optional. A list of base64-encoded images. Maximum 3 images allowed.
            max_tokens (int): Optional. The maximum number of tokens in the response. Default is 1000.
            options (dict[str: Any] | None): Optional. Additional options for the API request.

            Returns:
            tuple[str, int]: A tuple containing:
                - str: The generated response text or an error message.
                - int: Always 0 in the current implementation (placeholder for future use).

            Raises:
            Exception: If the API request fails or returns a non-200 status code.
        """
        if options is None:
            options = self.default_properties
        if images is not None and len(images) > 3:
            result = "Бот не может обработать больше 3-х картинок за раз!"
            return result, 0

        async with aiohttp.ClientSession() as session:
            # Limit the number of messages in history (for example, the last 10)
            limited_history = chat_history[-10:] if len(chat_history) > 10 else chat_history

            # Form `Messages`
            if not images:
                messages = [{"role": msg["role"], "content": msg["content"]} for msg in limited_history]
                messages.append({"role": "user", "content": user_prompt, "images": []})  # Добавляем новое сообщение
            else:
                messages = [{"role": msg["role"], "content": msg["content"]} for msg in limited_history]
                messages.append({"role": "user", "content": user_prompt, "images": images})  # Добавляем новое сообщение

            payload = {
                "model": self.model,
                "messages": messages,  # transmit the context in messages
                "stream": self.stream,
                "options": {
                    "num_predict": max_tokens,  # The maximum number of tokens in the response
                    **options
                }
            }

            async with session.post(f"{self.url}/chat", json=payload) as response:
                print(response)  # DELETE IN FUTURE
                if response.status == 200:
                    data = await response.json()
                    print(data)  # DELETE IN FUTURE
                    return data.get("message", "No response"), 0  # data.get('eval_count', 0)
                else:
                    error_text = await response.text()
                    raise Exception(f"Error {response.status}: {error_text}")

    async def encode_image_to_base64(self, image_path) -> str:
        """ Reads the image and converts it in Base64 """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
