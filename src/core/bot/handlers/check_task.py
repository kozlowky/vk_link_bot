import telebot
from django.utils import timezone
from telebot.types import CallbackQuery

from bot.constants.bot_label import BotLabel
from bot.constants.message_text import NO_VK_PAGE_IN_PROFILE, TASK_ACCEPTED_MANUALLY
from bot.utils.helpers import process_default_chat, process_advanced_chat
from core.bot.database.managers import user_db_manager
from core.bot.models import TaskStorage, LinksQueue, MessageLog


class TaskHandler:
    """ Класс для обработки сообщения с заданием """

    def __init__(self, callback: CallbackQuery, bot: telebot.TeleBot):
        """ Инициализация объекта TaskHandler """

        self.callback = callback
        self.bot = bot
        self.user = user_db_manager.get(callback.from_user.id)
        self.task = None
        self.chat_type = None

    def handle(self) -> None:
        """ Обработка сообщения с заданием. """

        if not self._check_user():
            return

        if not self._check_vk_url():
            return

        task_number = self._extract_task_number()

        if task_number is None:
            self.bot.send_message(
                chat_id=self.callback.message.chat.id,
                text="Не удалось извлечь номер задачи. Обратитесь к Администратору"
            )
            return

        self.task = TaskStorage.objects.filter(bot_user=self.user, order_number=task_number).last()

        if not self.task:
            self.bot.send_message(
                chat_id=self.callback.message.chat.id,
                text=f"Задача с номером {task_number} не найдена"
            )
            return
        self.chat_type = BotLabel(self.task.chat_type.chat_label).name
        MessageLog.objects.create(
            chat=self.task.chat_type,
            message_data=self.callback.json,
            created_at=timezone.now()
        )
        self.bot.edit_message_text(
            chat_id=self.callback.message.chat.id,
            message_id=self.callback.message.message_id,
            text="Проверяю задание... Ожидайте",
        )
        self._process_chat()

    def _check_user(self) -> bool:
        """ Проверяет наличие пользователя в базе данных. """

        if not self.user:
            self.bot.send_message(
                chat_id=self.callback.message.chat.id,
                text="Пользователь не найден"
            )
            return False
        return True

    def _check_vk_url(self) -> bool:
        """ Проверяет наличие привязанной страницы ВКонтакте у пользователя. """

        if not self.user.vk_user_url:
            self.bot.send_message(
                chat_id=self.callback.message.chat.id,
                text=NO_VK_PAGE_IN_PROFILE
            )
            return False
        return True

    def _extract_task_number(self) -> int:
        """ Извлекает номер задачи из текста сообщения. """

        text = self.callback.message.text
        index = text.find('№')

        if index == -1:
            return None

        task_number_part = text[index + 1:].strip()
        task_number_parts = task_number_part.split()

        if not task_number_parts:
            return None

        task_number = int(task_number_parts[0])
        return task_number

    def _process_chat(self) -> None:
        """Обрабатывает чат в зависимости от его типа (DEFAULT или ADVANCED)."""

        result = None

        if self.chat_type == "DEFAULT":
            result = process_default_chat(self.user, self.callback, self.task, self.bot)
        elif self.chat_type == "ADVANCED":
            result = process_advanced_chat(self.user, self.callback, self.task, self.bot)
        else:
            self._send_error_message()
            return

        if result:
            self._handle_success(result)

    def _send_error_message(self):
        """Отправляет сообщение об ошибке."""

        self.bot.send_message(
            chat_id=self.callback.message.chat.id,
            text="Произошла ошибка, обратитесь к Администратору",
            disable_web_page_preview=True
        )

    def _handle_success(self, result):
        """Обрабатывает успешное выполнение задачи."""

        result.task_completed = True
        result.save()
        approved_link = LinksQueue.objects.filter(result.link).last()
        if approved_link:
            approved_link.is_approved = True
            approved_link.save()
        self.bot.edit_message_text(
            chat_id=self.callback.message.chat.id,
            message_id=self.callback.message.message_id,
            text=f"{TASK_ACCEPTED_MANUALLY}",
            disable_web_page_preview=True
        )
