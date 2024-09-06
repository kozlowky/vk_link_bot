from django.conf import settings
from vk_api import vk_api

from core.bot.kb import KeyboardCreator
from core.bot.models import MessageText
from core.bot.utils.checker import VkChecker

vk = vk_api.VkApi(token=settings.VK_ACCESS_TOKEN).get_api()
checker_instance = VkChecker(vk)


class ChatProcessor:
    def __init__(self, user, callback, task, bot):
        self.user = user
        self.callback = callback
        self.task = task
        self.bot = bot
        self.messages = self._get_messages()
        self.data = self._run_advanced_chat()
        self.missing_values = self._get_missing_values()

    def _get_messages(self):
        return MessageText.objects.filter(key__in=["RESULT_MESSAGE", "USER_TASK_NUMBER"])

    def _run_advanced_chat(self):
        return checker_instance.run_advanced_chat(self.task, self.user)

    def _get_missing_values(self):
        missing_values = {}
        for item in self.data:
            for link, values in item.items():
                result = {key: False for key, value in values.items() if not value}
                if result:
                    missing_values[link] = result
        return missing_values

    def _get_message_dict(self):
        message_keys = []
        if any(values.get('comment') is False for values in self.missing_values.values()):
            message_keys.append("COMMENT_MISSING")
        if any(values.get('likes') is False for values in self.missing_values.values()):
            message_keys.append("LIKE_MISSING")
        if any(values.get('sub') is False for values in self.missing_values.values()):
            message_keys.append("SUBSCRIBE_MISSING")

        message_texts = MessageText.objects.filter(key__in=message_keys).values('key', 'message')
        return {msg['key']: msg['message'] for msg in message_texts}

    def _generate_error_messages(self, values, message_dict):
        error_messages = []
        if values.get('comment') is False:
            error_messages.append(message_dict.get("COMMENT_MISSING", ""))
        if values.get('likes') is False:
            error_messages.append(message_dict.get("LIKE_MISSING", ""))
        if values.get('sub') is False:
            error_messages.append(message_dict.get("SUBSCRIBE_MISSING", ""))
        return '\n\n'.join(error_messages)

    def _generate_results(self):
        message_dict = self._get_message_dict()
        results = {}

        for link, values in self.missing_values.items():
            error_messages = self._generate_error_messages(values, message_dict)
            results[link] = self.messages.get(key="RESULT_MESSAGE").message.format(value=error_messages)

        return results

    def _generate_result_string(self, results):
        user_number = self.messages.get(key="USER_TASK_NUMBER").message
        result_string = f"{user_number} {self.task.order_number}\n"
        for link, message in results.items():
            result_string += f"<a href='{link}'>{link}</a>:\n{message}\n"
        return result_string

    def _edit_message(self, result_string):
        check_kb = KeyboardCreator().create_check_keyboard()
        self.bot.edit_message_text(
            chat_id=self.callback.message.chat.id,
            message_id=self.callback.message.message_id,
            text=result_string,
            disable_web_page_preview=True,
            reply_markup=check_kb,
            parse_mode='HTML'
        )

    def process(self):
        if self.missing_values:
            results = self._generate_results()
            result_string = self._generate_result_string(results)
            self._edit_message(result_string)
        else:
            return self.task
