from bot.constants import message_text
from bot.constants.state_type import StateTypes
from bot.database.managers import user_db_manager
from bot.utils import state_worker
from bot.utils.helpers import get_status

from core.bot.kb import KeyboardCreator

keyboard_creator = KeyboardCreator()


def menu(message, bot):
    user = user_db_manager.get(user_id=message.from_user.id)
    if message.text == "Указать VK ID":
        state_worker.set_user_state(user, state=StateTypes.VK_LINK)
        bot.send_message(
            message.chat.id,
            text=message_text.LINK_ENTER
        )
    elif message.text == "Ввести ВИП код":
        state_worker.set_user_state(user, state=StateTypes.VIP_CODE)
        bot.send_message(
            message.chat.id,
            text=message_text.VIP_CODE_ENTER,
        )
    elif message.text == "Получить статус пользователя":
        # state_worker.set_user_state(user, state=StateTypes.GET_STATUS)
        result = get_status(user)
        if result:
            bot.send_message(
                message.chat.id,
                result,
                disable_web_page_preview=True
            )
