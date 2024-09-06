import telebot
from telebot import types

from core.bot.models import TaskStorage
from core.bot.handlers.start import keyboard_creator
from core.bot.handlers.check_task import TaskHandler

from core.bot.constants import message_text
from core.bot.database.managers import user_db_manager
from core.bot.handlers.decorator import ErrorHandler
from core.bot.utils.helpers import (
    get_last_task,
    process_accept_manually,
    remove_link_queue,
    get_help,
)

check_button = keyboard_creator.create_check_keyboard()
accept_button = keyboard_creator.create_accept_manualy()


@ErrorHandler.create()
def check(callback: types.CallbackQuery, bot: telebot.TeleBot) -> None:
    """ Функция для обработки callback-запросов бота. """

    handler = TaskHandler(callback, bot)
    handler.handle()

@ErrorHandler.create()
def accept(callback: types.CallbackQuery, bot: telebot.TeleBot) -> None:
    task_num = callback.message.text.split('№')[1].split('\n')[0].strip()
    task_instanse = TaskStorage.objects.get(order_number=task_num)
    task_instanse.task_completed = True
    task_instanse.save()
    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text='Задание переведено в статус "ВЫПОЛНЕНО"',
        disable_web_page_preview=True,
        parse_mode='HTML'
    )


@ErrorHandler.create()
def admin_commands(message: types.Message, bot):
    """ Функция для обработки комманд Администратора """

    user = user_db_manager.get(message.from_user.id)

    if user.is_admin:
        command, *args = message.text.split()
        if not args and command != '/help':
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

        if command == '/help':
            help_message = get_help() # todo будем хранить в БД
            bot.reply_to(
                message,
                text=help_message,
                disable_web_page_preview=True,
            )

        if result:
            bot.reply_to(
                message,
                text=result[0],
                disable_web_page_preview=True,
                reply_markup=check_button if result[1] == 'check' else accept_button,
            )
