import telebot
from telebot.types import Message

from bot.constants.message_text import (
    LINK_ADDED_FOR_NUMBER,
    TASK_IS_NOT_COMPLETE,
    LINK_COUNT_ERROR,
    NO_TASKS_NOW, USER_TASK_NUMBER
)
from bot.constants.users_type import UserTypes
from bot.database.managers import link_db_manager
from bot.kb import KeyboardCreator
from bot.utils.helpers import (
    check_message,
    create_link_for_preference,
    check_current_task,
    check_recent_objects,
    create_task_for_member
)


class ChatMemberHandler:
    def __init__(self, message: telebot.types.Message, bot: telebot.TeleBot, chat, user):
        """ Инициализация обработчика сообщений в группе. """

        self.bot = bot
        self.keyboard = KeyboardCreator().create_check_keyboard()
        self.link_data = check_message(message, chat)
        self.user = user
        self.chat = chat

    def handle_message(self, message: telebot.types.Message) -> None:
        """ Основной метод для обработки сообщений в группе. """

        if self._handle_link_errors(message, self.link_data):
            return

        if self._handle_admin_link(message, self.user, self.link_data):
            return

        if self._handle_current_task(message, self.user, self.chat):
            return

        if self._handle_recent_links(message, self.user, self.chat):
            return

        self._handle_vip_link(message, self.user, self.link_data)

        link = link_db_manager.create(obj=self.user, **self.link_data)
        self._assign_task_to_member(message, self.user, self.chat, link)

    def _handle_link_errors(self, message: Message, link_data: dict) -> bool:
        """ Обработка ошибок при проверке ссылки в сообщении. """

        if link_data.get('error'):
            self.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            self.bot.send_message(chat_id=message.from_user.id, text=link_data.pop('error'))
            return True
        return False

    def _handle_admin_link(self, message: Message, user, link_data: dict) -> bool:
        """ Обработка ссылок для администраторов. """

        if user.is_admin:
            link = create_link_for_preference(user, link_data)
            message_text = LINK_ADDED_FOR_NUMBER.format(
                link=link,
                number=link.queue_number
            )
            self.bot.send_message(
                chat_id=message.from_user.id,
                text=message_text,
                disable_web_page_preview=True
            )
            return True
        return False

    def _handle_current_task(self, message: Message, user, chat) -> bool:
        """ Обработка текущего незавершенного задания пользователя. """

        current_task = check_current_task(user, chat)
        if current_task:
            self.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            links = "\n".join([str(link) for link in current_task.links.all()])
            message_text = TASK_IS_NOT_COMPLETE.format(
                current_task=current_task.message_text,
                links=links
            )
            self.bot.send_message(
                chat_id=message.from_user.id,
                text=message_text,
                disable_web_page_preview=True,
                reply_markup=KeyboardCreator.create_check_keyboard()
            )
            return True
        return False

    def _handle_recent_links(self, message: Message, user, chat) -> bool:
        """ Обработка недавно добавленных ссылок. """

        allow_links = check_recent_objects(user, chat)
        if allow_links != 0:
            self.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            message_text = LINK_COUNT_ERROR.format(
                link=message.text,
                count=chat.reply_link_count,
                allow_links=allow_links
            )
            self.bot.send_message(
                chat_id=message.from_user.id,
                text=message_text,
                disable_web_page_preview=True
            )
            return True
        return False

    def _handle_vip_link(self, message: Message, user, link_data: dict):
        """ Обработка ссылок для пользователей со статусом VIP. """

        if user.status == UserTypes.VIP:
            link = create_link_for_preference(user, link_data)
            message_text = LINK_ADDED_FOR_NUMBER.format(
                link=link,
                number=link.queue_number
            )
            self.bot.send_message(
                chat_id=message.from_user.id,
                text=message_text,
                disable_web_page_preview=True
            )

    def _assign_task_to_member(self, message: Message, user, chat, link):
        """ Назначение задания для пользователя. """

        task = create_task_for_member(user, chat, link)
        if task:
            links = [link.vk_link for link in task.links.all()]
            links_message = "\n".join(links)

            self.bot.send_message(
                chat_id=message.from_user.id,
                text=f"{USER_TASK_NUMBER + str(task.order_number)}\n{links_message}",
                disable_web_page_preview=True,
                reply_markup=KeyboardCreator().create_check_keyboard()
            )

        else:
            message_text = NO_TASKS_NOW.format(
                number=link.queue_number
            )
            self.bot.send_message(
                chat_id=message.from_user.id,
                text=message_text
            )
