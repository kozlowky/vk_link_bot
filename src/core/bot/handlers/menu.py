from core.bot.constants.users_type import UserTypes
from core.bot.models import MessageText
from core.bot.constants.state_type import StateTypes
from core.bot.database.managers import user_db_manager
from core.bot.utils import state_worker
from core.bot.utils.helpers import get_status

from core.bot.kb import KeyboardCreator

keyboard_creator = KeyboardCreator()


def menu(message, bot):
    user = user_db_manager.get(user_id=message.from_user.id)
    if message.text == "Указать VK ID":
        state_worker.set_user_state(user, state=StateTypes.VK_LINK)
        bot.send_message(
            message.chat.id,
            text=MessageText.objects.get(key="LINK_ENTER").message
        )
    elif message.text == "Ввести ВИП код":
        if user.status != UserTypes.VIP:
            state_worker.set_user_state(user, state=StateTypes.VIP_CODE)
            bot.send_message(
                message.chat.id,
                text=MessageText.objects.get(key="VIP_CODE_ENTER").message
            )
        else:
            bot.reply_to(
                message=message,
                text=MessageText.objects.get(key="VIP_CODE_EXSISTS").message
            )
    elif message.text == "Получить статус пользователя":
        result = get_status(user)
        if result:
            bot.send_message(
                message.chat.id,
                result,
                disable_web_page_preview=True
            )
