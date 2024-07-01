import logging
import traceback
from typing import Union

from telebot import logger
from telebot.types import CallbackQuery, Message

logger = logger
logger.setLevel(logging.DEBUG)


class ErrorHandler:
    """Класс-декоратор обработки ошибок в хэндлерах бота."""

    def __init__(self, callback):
        """Определение функции хэндлера как аргумента."""
        self.callback = callback

    def __call__(
            self,
            message,
            bot,
    ):
        """Вызов хэндлера."""
        try:
            self.callback(message, bot)
        except Exception:
            trace = traceback.format_exc()
            return self._on_failure(
                message=message,
                bot=bot,
                trace=trace,
            )

    def _on_failure(
            self,
            message,
            bot,
            trace,
    ):
        """Метод обработки ошибки вызова хэндлера."""
        logger.error(trace)
        text = "ЧТО-ТО ПОШЛО НЕ ТАК ОБРАТИТЕСЬ К АДМИНИСТРАТОРУ"
        # keyboard = KeyboardConstructor().create_menu_keyboard()

        try:
            chat_id = message.message.chat.id
        except AttributeError:
            chat_id = message.chat.id

        return bot.send_message(
            chat_id=chat_id,
            text=text,
            # reply_markup=keyboard,
        )

    @classmethod
    def create(cls):
        """Декоратор для создания экземпляра хэндлера."""

        def decorator(function):
            def wrapper(
                    message,
                    bot,
            ):
                result = cls(function)
                return result(message, bot)

            return wrapper

        return decorator
