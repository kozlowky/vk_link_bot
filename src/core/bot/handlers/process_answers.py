from bot.constants import message_text
from bot.constants.state_type import StateTypes

from bot.database.managers import user_db_manager

from bot.handlers.start import keyboard_creator
from bot.handlers.chats import ChatMemberHandler
from bot.utils import state_worker
from bot.utils.helpers import (
    process_vk_link,
    process_vip_code,
    get_chat
)


def process_answers(message, bot):
    user = user_db_manager.get(user_id=message.from_user.id)
    state_type = user.state_menu

    if state_type == StateTypes.VK_LINK.value:
        result = process_vk_link(message, user, bot)
        if result:
            bot.reply_to(
                message=message,
                text=result,
                disable_web_page_preview=True
            )
        state_worker.set_user_state(user, state=StateTypes.DEFAULT)

    if state_type == StateTypes.VIP_CODE.value:
        result = process_vip_code(message, user)
        if result:
            bot.reply_to(
                message=message,
                text=result,
                reply_markup=keyboard_creator.create_user_keyboard()
            )

    if message.text == "Нет ВИП кода":
        state_worker.set_user_state(user, state=StateTypes.DEFAULT)

        bot.reply_to(
            message=message,
            text=message_text.AUTH_USER,
            disable_web_page_preview=True,
            reply_markup=keyboard_creator.create_user_keyboard()
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
            ChatMemberHandler(message, bot, chat, user).handle_message(message)
