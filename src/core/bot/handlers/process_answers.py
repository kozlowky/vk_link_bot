from celery.result import AsyncResult

from core.bot.handlers.decorator import ErrorHandler
from core.bot.constants import message_text
from core.bot.constants.state_type import StateTypes

from core.bot.database.managers import user_db_manager
from core.bot.tasks import handle_message_task
from core.bot.handlers.start import keyboard_creator
from core.bot.models import MessageText
from core.bot.utils import state_worker
from core.bot.utils.helpers import (
    process_vk_link,
    process_vip_code,
    get_chat
)

user_keyboard = keyboard_creator.create_user_keyboard()
check_button = keyboard_creator.create_check_keyboard()


@ErrorHandler.create()
# todo ошибки state организовать сброс
# todo рефакторинг
def process_answers(message, bot):
    user = user_db_manager.get(user_id=message.from_user.id)
    state_type = user.state_menu

    if state_type == StateTypes.VK_LINK.value:
        result = process_vk_link(message, user)
        if isinstance(result, MessageText):
            bot.reply_to(
                message=message,
                text=result.message,
                disable_web_page_preview=True
            )
        state_worker.set_user_state(user, state=StateTypes.DEFAULT)
        bot.reply_to(
            message=message,
            text=result,
            disable_web_page_preview=True
        )

    if state_type == StateTypes.VIP_CODE.value:
        result = process_vip_code(message, user)
        if result:
            bot.reply_to(
                message=message,
                text=result,
                reply_markup=user_keyboard,
                parse_mode="HTML"
            )

    if message.text == "Нет ВИП кода":
        state_worker.set_user_state(user, state=StateTypes.DEFAULT)

        bot.reply_to(
            message=message,
            text=message_text.AUTH_USER,
            disable_web_page_preview=True,
            reply_markup=user_keyboard
        )

    if message.chat.type in ['group', 'supergroup']:
        state_worker.set_user_state(user, state=StateTypes.DEFAULT)
        chat = get_chat(message)

        if not user.vk_user_url:
            bot.delete_message(
                chat_id=message.chat.id,
                message_id=message.message_id
            )

            bot.send_message(
                chat_id=message.from_user.id,
                text=message_text.NO_VK_PAGE_IN_PROFILE
            )

            return

        if chat:
            result = handle_message_task.delay(message.json)
            data = AsyncResult(result.id).get(timeout=10)
            if data.get("result"):
                bot.send_message(
                    chat_id=message.from_user.id,
                    text=data["result"],
                    reply_markup=check_button if data.get("markup") else None,
                    disable_web_page_preview=True
                )
