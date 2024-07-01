from core.bot.models import MessageText
from core.bot.constants.message_text import (
    LINK_ADDED_FOR_NUMBER,
    TASK_IS_NOT_COMPLETE,
    NO_TASKS_NOW, USER_TASK_NUMBER
)
from core.bot.constants.users_type import UserTypes
from core.bot.database.managers import link_db_manager
from core.bot.utils.helpers import (
    check_message,
    create_link_for_preference,
    check_current_task,
    check_recent_objects,
    create_task_for_member
)


class ChatMemberHandler:
    def __init__(self, chat, user):
        """ Инициализация обработчика сообщений в чате. """

        self.user = user
        self.chat = chat
        self.message_text_qs = MessageText.objects.filter(
            key__in=[
                "LINK_ADDED_FOR_NUMBER",
                "TASK_IS_NOT_COMPLETE",
                "USER_TASK_NUMBER",
                "NO_TASKS_NOW"
            ]
        )

    def handle_message(self, message):
        """ Метод обработки сообщений в группе. """

        link_data = check_message(message, self.chat)

        if link_data.get('error'):
            return {"result": link_data["error"]}

        if self.user.is_admin or self.user.status == UserTypes.VIP:
            link = create_link_for_preference(self.user, link_data)
            link_add_number = self.message_text_qs.get(key="LINK_ADDED_FOR_NUMBER").message
            message_text = link_add_number.format(
                link=link,
                number=link.queue_number
            )
            return {"result": message_text}

        current_task = check_current_task(self.user, self.chat)
        if current_task:
            links = "\n".join([str(link) for link in current_task.links.all()])
            message_text = TASK_IS_NOT_COMPLETE.format(
                current_task=current_task.order_number,
                links=links
            )
            return {"result": message_text, "markup": True}
        # TODO не правильно работает check_recent_objects
        allow_links = check_recent_objects(self.user, self.chat)
        if allow_links != 0:
            link_count_error = MessageText.objects.get(key="LINK_COUNT_ERROR").message
            message_text = link_count_error.format(
                link=message["text"],
                count=self.chat.reply_link_count,
                allow_links=allow_links
            )
            return {"result": message_text}

        link = link_db_manager.create(obj=self.user, **link_data)
        task = create_task_for_member(self.user, self.chat, link)
        if task:
            task_urls = {}
            for link in task.links.all():
                link_url = link.vk_link
                link_comment = link.comment if link.comment else ""
                task_urls[link.id] = {"URL": link_url, "COMMENT": link_comment}

            links_message = "\n".join(
                [
                    f"{i + 1}. {details['URL']}" + (
                        f", Комментарий: {details['COMMENT']}" if details['COMMENT'] else "")
                    for i, (link_id, details) in enumerate(task_urls.items())
                ]
            )

            user_task_number = self.message_text_qs.get(key="USER_TASK_NUMBER").message
            message_text = f"{user_task_number + str(task.order_number)}\n{links_message}"
            return {"result": message_text, "markup": True}

        no_tasks = self.message_text_qs.get(key="NO_TASKS_NOW").message
        message_text = no_tasks.format(
            number=link.queue_number
        )
        return {"result": message_text}
