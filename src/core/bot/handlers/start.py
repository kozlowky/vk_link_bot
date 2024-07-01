from telebot import types

from core.bot.handlers.decorator import ErrorHandler
from core.bot.constants import message_text
from core.bot.database.managers import user_db_manager
from core.bot.kb import KeyboardCreator

keyboard_creator = KeyboardCreator()
start_keyboard = keyboard_creator.create_start_keyboard()


@ErrorHandler.create()
def start(message: types.Message, bot):
    user_id = message.from_user.id
    user = user_db_manager.get(user_id)
    if user:
        bot.reply_to(
            message,
            text=message_text.AUTH_USER,
            reply_markup=keyboard_creator.create_user_keyboard()
        )
    else:
        user_data = {
            "first_name": message.from_user.first_name,
            "last_name": message.from_user.last_name,
            "username": message.from_user.username,
        }
        user_db_manager.create(user_id, **user_data)

        bot.reply_to(
            message,
            text=message_text.START_MESSAGE,
            reply_markup=start_keyboard
        )
