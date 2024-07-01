import telebot
from telebot import types

from core.bot.handlers.check_task import TaskHandler

from core.bot.constants import message_text
from core.bot.database.managers import user_db_manager
from core.bot.handlers.decorator import ErrorHandler
from core.bot.utils.helpers import (
    get_last_task,
    process_accept_manually,
    remove_link_queue
)


@ErrorHandler.create()
def check(callback: types.CallbackQuery, bot: telebot.TeleBot) -> None:
    """ Функция для обработки callback-запросов бота. """

    handler = TaskHandler(callback, bot)
    handler.handle()


@ErrorHandler.create()
def admin_commands(message: types.Message, bot):
    """ Функция для обработки комманд Администратора """

    user = user_db_manager.get(message.from_user.id)

    if user.is_admin:
        command, *args = message.text.split()
        if not args:
            bot.reply_to(
                message,
                text=message_text.WRONG_FORMAT,
                disable_web_page_preview=True,
            )
            return
        data = ' '.join(args)

        command_functions = {
            '/get_task': get_last_task,
            '/accept_task': process_accept_manually,
            '/remove_link': remove_link_queue
        }

        result = None
        if command in command_functions:
            result = command_functions[command](data)

        if result:
            bot.reply_to(
                message,
                text=result,
                disable_web_page_preview=True,
            )
