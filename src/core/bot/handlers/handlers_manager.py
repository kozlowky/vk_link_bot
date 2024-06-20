import telebot
from telebot import types

from bot.handlers.check_task import TaskHandler

from bot.constants import message_text
from bot.database.managers import user_db_manager
from bot.utils.helpers import get_last_task, process_accept_manually, remove_link_queue


def check(callback: types.CallbackQuery, bot: telebot.TeleBot) -> None:
    """ Функция для обработки callback-запросов бота. """

    handler = TaskHandler(callback, bot)
    handler.handle()


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
