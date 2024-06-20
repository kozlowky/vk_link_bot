from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from telebot import types

from vk_api import vk_api

from bot.constants import message_text
from bot.constants.message_text import (
    VIP_CODE_SUCESS,
    MEMBER_STATUS,
    VK_PAGE_ALREADY_EXSIST,
    RESULT_MESSAGE,
    SUBSCRIBE_MISSING,
    COMMENT_MISSING,
    LIKE_MISSING, USER_TASK_NUMBER, TASK_ACCEPTED_MANUALLY
)
from bot.constants.state_type import StateTypes
from bot.database.managers import user_db_manager, link_db_manager
from bot.kb import KeyboardCreator
from bot.utils import state_worker
from bot.utils.checker import VkChecker
from core.bot.constants.users_type import UserTypes

from core.bot.models import Chat, TaskStorage, LinksQueue, VIPCode, MessageText

vk = vk_api.VkApi(token=settings.VK_ACCESS_TOKEN).get_api()


def get_chat(message: types.Message) -> Chat:
    """ Получает чат """

    chat = Chat.objects.get(
        bot_chats=f'https://t.me/{message.chat.username}'
    )
    chat_id = message.chat.id

    if chat.chat_id != chat_id:
        chat.chat_id = chat_id
        chat.save(update_fields=['chat_id'])

    return chat


def check_message(message: types.Message, chat) -> dict:
    """ Проверяет корректность отправленной ссылки в чат """

    result = {}

    if not message.entities or message.entities[0].type != 'url':
        result.update({'error': message_text.WRONG_URL_FORMAT})
        return result

    if 'wall' not in message.text:
        result.update({'error': message_text.WRONG_URL_FORMAT})
        return result

    link_count = message.text.count('vk.com')
    if link_count != 1:
        result.update({'error': message_text.ONLY_ONE_LINK_TO_SEND})
        return result

    rest_of_link = message.text.split("wall")[1]
    parts = rest_of_link.split("_")
    owner_id = parts[0]
    post_id = parts[1]
    split_post_id = post_id.split(maxsplit=1)
    if len(split_post_id) > 1:
        post_id = split_post_id[0]
        result.update({'comment': split_post_id[1]})

    result.update(
        {
            'vk_link': settings.VK_URL + owner_id + "_" + post_id,
            'owner_id': owner_id,
            'post_id': post_id,
            "total_count": chat.link_count,
            "chat_type": chat,
        }
    )

    return result


def check_recent_objects(user, chat) -> int:
    """ Проверяет очередь ссылки перед сохранением """

    allow_link_count = chat.reply_link_count

    links_exists = LinksQueue.objects.filter(
        chat_type=chat,
        bot_user=user.id
    ).exists()

    if links_exists:
        links_allow_qs = list(
            LinksQueue.objects.filter(
                chat_type=chat,
            ).order_by("-approved_at")[:allow_link_count]
        )

        user_in_qs = any(user.id == link.bot_user_id for link in links_allow_qs)

        if user_in_qs:
            total_links = 0
            index_bot_user_ids = [(index, link.bot_user_id) for index, link in enumerate(links_allow_qs, start=0)]
            for index, user_id in index_bot_user_ids:
                if user_id == user.id:
                    total_links = allow_link_count - index
            return total_links

    return 0


# TODO Проверяем действует ли VIP статус
def check_current_task(user, chat):
    """ Проверяет наличие не завершенных задач """

    if user.status != UserTypes.VIP:

        ts_qs = TaskStorage.objects.filter(
            bot_user=user.id,
            chat_type=chat,
            task_completed=False
        ).last()

        if ts_qs:
            return ts_qs

    return None


def accept_send_task(user_id):
    """ Сохраняет ссылку в случае если задание принято """

    links_qs = LinksQueue.objects.filter(bot_user=user_id).last()
    vk_link = links_qs.vk_link
    links_qs.is_approved = True
    accepted_task = TaskStorage.objects.filter(bot_user=user_id, task_completed=False).last()
    accepted_task.task_completed = True
    links_qs.save()
    accepted_task.save()
    LinksQueue.objects.create(bot_user=user_id, vk_link=vk_link)

    return message_text.TASK_ACCEPTED_MANUALLY


def get_last_task(data):
    """ Получает последнее задание пользователя """

    user = user_db_manager.filter(vk_user_url=data)
    if user:
        ts_qs = TaskStorage.objects.filter(
            bot_user__vk_user_url=data,
            task_completed=False
        )
        if not ts_qs.exists():
            message = message_text.NO_CURRENT_TASK
        else:
            last_chat_type = ts_qs.last()
            message = last_chat_type.message_text
    else:
        message = f"Пользователь: {data} не существует!"

    return message


def process_accept_manually(data):
    """ Принимает выполнение задачи вручную """

    user = user_db_manager.filter(vk_user_url=data)
    if user:
        ts_qs = TaskStorage.objects.filter(
            bot_user__vk_user_url=data,
            task_completed=False
        )
        if not ts_qs.exists():
            message = f"У пользователя {data} нет заданий"

        else:
            last_task = ts_qs.last()
            message = f"Пользователь {data}\n\n{last_task.message_text}"
    else:
        message = f"Пользователь: {data} не существует!"

    return message


def remove_link_queue(data):
    """ Удаляет последнюю ссылку из очереди """

    link = LinksQueue.objects.filter(vk_link=data).last()
    if link:
        link.delete()
        return True

    return None


def process_vk_link(message, user, bot):
    vk_page_url = message.text
    checker_instance = VkChecker(vk, bot)
    if user.vk_user_url == vk_page_url:
        return VK_PAGE_ALREADY_EXSIST.format(
            vk_page_url=vk_page_url
        )

    if 'vk.com/' in vk_page_url:
        vk_id = checker_instance.get_user_id(vk_page_url)
        if vk_id:
            user.vk_id = vk_id
            user.vk_user_url = vk_page_url
            user.save()
            return message_text.VK_PAGE_SUCESS

        return message_text.VK_PAGE_ERROR


def get_status(user):
    """ Получает статус пользователя """

    return MEMBER_STATUS.format(
        url=user.vk_user_url,
        status=user.get_status_display(),
        tg_id=user.tg_id
    )


def process_vip_code(message, user):
    """ Проверяет наличие и валидность ВИП-кода пользователя.
        Добавляет ВИП-код пользователю. """

    vip_code_user_value = message.text
    vip_code_instance_exists = VIPCode.objects.filter(vip_code=vip_code_user_value).exists()
    if vip_code_instance_exists:
        state_worker.set_user_state(user, state=StateTypes.DEFAULT)
        vip_code_instance = VIPCode.objects.get(vip_code=vip_code_user_value)
        user_vip_code = user.vip_code

        if user_vip_code:
            return message_text.VIP_CODE_EXSISTS

        user.vip_code = vip_code_instance
        user.status = UserTypes.VIP
        user.vip_end_date = timezone.now() + timedelta(days=30)
        vip_code_end_date = user.vip_end_date.strftime("%d.%m.%Y")

        return VIP_CODE_SUCESS.format(
            vip_code_end_date=vip_code_end_date
        )

    return message_text.WRONG_VIP_CODE


def create_link_for_preference(user, link_data):
    """ Создает объект Link принудительно """

    link_data.update({"is_approved": True})
    link = link_db_manager.create(
        obj=user,
        **link_data
    )

    return link


# TODO Переделать.
def create_task_for_member(user, chat, link):
    """ Создает задачу для пользователя """

    # TODO Тест с комментариями
    tasks_qs = list(
        LinksQueue.objects.exclude(
            bot_user_id=user.id
        ).filter(
            chat_type=chat,
            is_approved=True,
        ).distinct()
    )

    if tasks_qs:
        task_links = [task.vk_link for task in tasks_qs]
        new_task = TaskStorage.objects.create(
            link=link,
            bot_user=user,
            chat_type=chat,
        )
        for task in tasks_qs:
            task.send_count += 1
            link_db_manager.update(link_id=task.id, send_count=task.send_count)

            new_task.links.add(task)

        new_task.save()

        return new_task


def process_default_chat(user_id, callback, task_code):
    a = task_code
    data = checker_instance.run_default_chat(callback.message, user_id)
    posts_without_like = []

    for item in data:
        link = item.get('link')
        likes = item.get('likes')

        if not likes:
            posts_without_like.append(link)

        tasks_qs = list(LinksQueue.objects.all().values())

        for task in tasks_qs:
            if task['vk_link'] == link and link not in posts_without_like:
                task_instance = LinksQueue.objects.get(id=task['id'])
                UserDoneLinks.objects.get_or_create(bot_user=user_id, link=task_instance)

    if posts_without_like:
        message = f"Задание № {task_code}\n\nВы не поставили лайк в следующих постах:\n\n"
        message += "\n".join(posts_without_like)

        try:
            TaskStorage.objects.filter(code=task_code).update(message_text=message)
            bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=message,
                disable_web_page_preview=True,
                reply_markup=check_kb
            )
        except ApiTelegramException:
            message_ext = f"Вы не завершили предыдущее {message}"
            bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=message_ext,
                disable_web_page_preview=True,
                reply_markup=check_kb
            )
            TaskStorage.objects.filter(code=task_code).update(message_text=message_ext)
    else:
        message = accept_send_task(user_id)
        bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=message,
            disable_web_page_preview=True
        )


# TODO ALL REFACTORING!!!!
def process_advanced_chat(user, callback, task, bot):
    checker_instance = VkChecker(vk, bot)
    data = checker_instance.run_advanced_chat(task, user)
    missing_values = {}
    for item in data:
        for link, values in item.items():
            result = {key: False for key, value in values.items() if not value}
            if result:
                missing_values[link] = result

    results = {}

    if missing_values:
        message_keys = []
        if any(values.get('comment') is False for values in missing_values.values()):
            message_keys.append("COMMENT_MISSING")
        if any(values.get('likes') is False for values in missing_values.values()):
            message_keys.append("LIKE_MISSING")
        if any(values.get('sub') is False for values in missing_values.values()):
            message_keys.append("SUBSCRIBE_MISSING")

        message_texts = MessageText.objects.filter(key__in=message_keys).values('key', 'message')
        message_dict = {msg['key']: msg['message'] for msg in message_texts}

        for link, values in missing_values.items():
            error_messages = []
            if values.get('comment') is False:
                error_messages.append(message_dict.get("COMMENT_MISSING", ""))
            if values.get('likes') is False:
                error_messages.append(message_dict.get("LIKE_MISSING", ""))
            if values.get('sub') is False:
                error_messages.append(message_dict.get("SUBSCRIBE_MISSING", ""))

            value = '\n\n'.join(error_messages)
            results[link] = RESULT_MESSAGE.format(value=value)

        result_string = f"{USER_TASK_NUMBER} {task.order_number}\n"
        for link, message in results.items():
            result_string += f"{link}:{message}\n"

        check_kb = KeyboardCreator().create_check_keyboard()
        bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=result_string,
            disable_web_page_preview=True,
            reply_markup=check_kb
        )

    else:
        return task
