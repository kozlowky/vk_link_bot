import logging
import telebot
import vk_api

from django.conf import settings

from bot.constants import buttons
from bot.handlers.handlers_manager import (
    admin_commands,
    check,
)
from bot.handlers.menu import menu
from bot.handlers.process_answers import process_answers
from bot.handlers.start import start

from bot.utils.user_mute import UserHandler

bot = telebot.TeleBot(
    settings.TOKEN_BOT,
    parse_mode='HTML'
)

telebot.logger.setLevel(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

user_handler = UserHandler(bot)

MESSAGE_HANDLERS_MAP = {
    start: {
        'commands': ['start'],
    },
    admin_commands: {
        'commands': ['get_task', 'accept_task'],
    },
    menu: {
        'func': lambda message: message.text in [
            buttons.SET_VK_ID,
            buttons.ENTER_VIP_CODE,
            buttons.GET_USER_STATUS
        ],
    },
    process_answers: {
        'content_types': ['text'],
    },
}

CALLBACK_HANDLERS_MAP = {
    check: {
        'func': lambda callback: callback.data == 'check_button',
    },
}


def register_handlers():
    """Функция регистрации обработчиков бота."""

    for func, params in MESSAGE_HANDLERS_MAP.items():
        bot.register_message_handler(
            func,
            **params,
            pass_bot=True,
        )

    for func, params in CALLBACK_HANDLERS_MAP.items():
        bot.register_callback_query_handler(
            func,
            **params,
            pass_bot=True,
        )


register_handlers()

#

#
#
# @bot.callback_query_handler(func=lambda callback: callback.data == 'accept_manually')
# def manual_accept_task(callback: telebot.types.CallbackQuery):
#     """
#     Ручное принятие задания
#     """
#     task_message = callback.message.text
#     user_id = re.search(r'Пользователь (\S+)', task_message).group(1)
#     task_code = re.search(r'№ (\S+)(?::)', task_message).group(1)
#     sender_user = BotUser.objects.get(tg_id=callback.from_user.id)
#     target_user = BotUser.objects.get(tg_id=user_id)
#
#     task = TaskStorage.objects.get(code=task_code)
#     task.task_completed = True
#     task.save()
#
#     link_storage = LinkStorage.objects.get(code=task_code)
#     link_storage.is_approved = True
#     link_storage.save()
#
#     link = link_storage.vk_link
#     link_queue = LinksQueue.objects.create(bot_user=target_user, vk_link=link)
#     link_queue.save()
#
#     done_link = UserDoneLinks.objects.create(bot_user=target_user, link=link_queue)
#     done_link.save()
#
#     bot.send_message(
#         chat_id=callback.message.chat.id,
#         text=f"Задание № {task_code} переведено в статус ВЫПОЛНЕНО")
#     state_worker.reset_user_state(sender_user)
