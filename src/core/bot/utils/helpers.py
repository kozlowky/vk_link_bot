from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from telebot import types
from vk_api import vk_api

from core.bot.constants.state_type import StateTypes
from core.bot.constants.users_type import UserTypes, status_display
from core.bot.database.managers import link_db_manager, user_db_manager
from core.bot.handlers.advanced_chat_processors import ChatProcessor
from core.bot.kb import KeyboardCreator
from core.bot.models import Chat, LinksQueue, MessageText, TaskStorage, VIPCode
from core.bot.utils import state_worker
from core.bot.utils.checker import VkChecker

vk = vk_api.VkApi(token=settings.VK_ACCESS_TOKEN).get_api()
checker_instance = VkChecker(vk)


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


def check_message(message, chat) -> dict:
    """ Проверяет корректность отправленной ссылки в чат """

    result = {}

    message_entities = message.get("entities")

    if message_entities and any(entity.get("type") != 'url' for entity in message_entities):
        result.update(
            {
                'error': MessageText.objects.get(key="WRONG_URL_FORMAT").message
            }
        )
        return result

    message_text = message.get("text")

    if message_text and 'wall' not in message_text:
        result.update(
            {
                'error': MessageText.objects.get(key="WRONG_URL_FORMAT").message
            }
        )
        return result

    link_count = message_text.count('vk.com')
    if link_count != 1:
        result.update(
            {
                'error': MessageText.objects.get(key="ONLY_ONE_LINK_TO_SEND").message
            }
        )
        return result

    rest_of_link = message_text.split("wall")[1]
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
            ).order_by("-approved_at")
        )

        links_allow_qs_sliced = links_allow_qs[:allow_link_count]

        user_in_qs = any(user.id == link.bot_user.id for link in links_allow_qs_sliced)

        if user_in_qs:
            total_links = 0
            index_bot_user_ids = [(index, link.bot_user_id) for index, link in
                                  enumerate(links_allow_qs_sliced, start=0)]
            for index, user_id in index_bot_user_ids:
                if user_id == user.id:
                    total_links = allow_link_count - index
            return total_links

    return 0


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
    message = MessageText.objects.get(key="TASK_ACCEPTED_MANUALLY")
    return message


def get_last_task(data):
    """ Получает последнее задание пользователя """

    user = user_db_manager.filter(vk_user_url=data)
    if user:
        ts_qs = TaskStorage.objects.filter(
            bot_user__vk_user_url=data,
            task_completed=False
        )
        if not ts_qs.exists():
            message = MessageText.objects.get(key="NO_CURRENT_TASK")
        else:
            task = ts_qs.last()
            links_in_task = task.links.values_list("vk_link", flat=True)
            links_message = "\n".join([f"{index + 1}. {link}" for index, link in enumerate(links_in_task)])
            message_text = MessageText.objects.get(key="USER_TASK_NUMBER").message
            message = f"{message_text}{task.order_number}\n{links_message}", 'check'
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
            links_in_task = last_task.links.values_list("vk_link", flat=True)
            links_message = "\n".join([f"{index + 1}. {link}" for index, link in enumerate(links_in_task)])
            message_text = MessageText.objects.get(key="USER_TASK_NUMBER").message
            message = f"{message_text}{last_task.order_number}\n{links_message}", 'accept'
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


def get_help():
    return ''' 
    /get_task - выводит активное задание пользователя 
/accept_task - принимает задание пользователя
/remove_link - удаляет ссылку пользователя
    '''


def process_vk_link(message, user):
    vk_page_url = message.text.strip()

    if user.vk_user_url == vk_page_url:
        return MessageText.objects.get(
            key="VK_PAGE_ALREADY_EXSIST"
        ).message.format(
            vk_page_url=vk_page_url
        )

    if 'vk.com/' in vk_page_url:
        separator = ' '
        index_separator = vk_page_url.find(separator)

        if index_separator != -1:
            url_part = vk_page_url[:index_separator].strip()
            other_part = vk_page_url[index_separator + len(separator):].strip()
        else:
            url_part = vk_page_url.strip()
            other_part = None

        if other_part is not None:
            return MessageText.objects.get(key="VK_PAGE_ERROR")

        vk_id = checker_instance.get_user_id(url_part)
        if vk_id:
            user.vk_id = vk_id
            user.vk_user_url = url_part
            user.save()
            message_text = MessageText.objects.get(
                key="VK_PAGE_SUCCESS"
            ).message
        else:
            message_text = MessageText.objects.get(key="VK_PAGE_ERROR")
    else:
        message_text = MessageText.objects.get(key="WRONG_URL_FORMAT")

    return message_text


def get_status(user):
    """ Получает статус пользователя """

    message_text = MessageText.objects.get(key="MEMBER_STATUS").message
    return message_text.format(
        url=user.vk_user_url,
        status=status_display(user),
        tg_id=user.tg_id
    )


def process_vip_code(message, user):
    """ Проверяет наличие и валидность ВИП-кода пользователя.
        Добавляет ВИП-код пользователю. """

    vip_code_instance = VIPCode.objects.filter(vip_code=message.text).first()

    if vip_code_instance:
        update_data = {
            "state_menu": state_worker.set_user_state(user, state=StateTypes.DEFAULT),
            "vip_code": vip_code_instance,
            "status": UserTypes.VIP,
            "vip_end_date": timezone.now() + timedelta(days=30),
        }

        user_db_manager.filter(id=user.id).update(**update_data)

        message_text = MessageText.objects.get(key="VIP_CODE_SUCCESS").message
        return message_text.format(
            vip_code_end_date=update_data["vip_end_date"].strftime("%d.%m.%Y")
        )

    return MessageText.objects.get(key="WRONG_VIP_CODE").message


def create_link_for_preference(user, link_data):
    """ Создает объект Link принудительно """

    link_data.update({"is_approved": True})
    link = link_db_manager.create(
        obj=user,
        **link_data
    )

    return link


def create_task_for_member(user, chat, link):
    """ Создает задачу для пользователя """

    if user.status != UserTypes.VIP:
        tasks_qs = list(
            LinksQueue.objects.exclude(
                bot_user_id=user.id
            ).filter(
                chat_type=chat,
                is_approved=True,
            ).distinct()
        )

        if tasks_qs:
            new_task = TaskStorage.objects.create(
                link=link,
                bot_user=user,
                chat_type=chat,
            )

            max_links = chat.task_link_count
            limited_tasks_qs = tasks_qs[:max_links]

            for task in limited_tasks_qs:
                task.send_count += 1
                link_db_manager.update(link_id=task.id, send_count=task.send_count)

                new_task.links.add(task)

            new_task.save()

            return new_task

    return 'vip' # todo вернуть объект

# todo удалить
def process_default_chat(user, callback, task, bot):
    messages = MessageText.objects.filter(key__in=["RESULT_MESSAGE", "USER_TASK_NUMBER"])
    data = checker_instance.run_default_chat(task, user)
    posts_without_like = []
    for item in data:
        link = item.get('link')
        likes = item.get('likes')

        if not likes:
            posts_without_like.append(link)

    if posts_without_like:

        message_texts = MessageText.objects.filter(key="LIKE_MISSING").values('key', 'message')
        message_dict = {msg['key']: msg['message'] for msg in message_texts}

        for link in posts_without_like:
            value = '\n\n'.join(error_messages)
            results[link] = messages.get(key="RESULT_MESSAGE").message.format(value=value)
        user_number = messages.get(key="USER_TASK_NUMBER").message
        result_string = f"{user_number} {task.order_number}\n"
        for link, message in results.items():
            result_string += f"<a href='{link}'>Ссылка</a>:\n{message}\n"

        check_kb = KeyboardCreator().create_check_keyboard()
        bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=result_string,
            disable_web_page_preview=True,
            reply_markup=check_kb,
            parse_mode='HTML'
        )

        pass

    missing_values = {}
    for item in data:

        for link, values in item.items():
            result = {key: False for key, value in values.items() if not value}
            if result:
                missing_values[link] = result

    results = {}

    if missing_values:
        message_keys = []
        if any(values.get('likes') is False for values in missing_values.values()):
            message_keys.append("LIKE_MISSING")

        message_texts = MessageText.objects.filter(key__in=message_keys).values('key', 'message')
        message_dict = {msg['key']: msg['message'] for msg in message_texts}

        for link, values in missing_values.items():
            error_messages = []

            if values.get('likes') is False:
                error_messages.append(message_dict.get("LIKE_MISSING", ""))

            value = '\n\n'.join(error_messages)
            results[link] = messages.get(key="RESULT_MESSAGE").message.format(value=value)
        user_number = messages.get(key="USER_TASK_NUMBER").message
        result_string = f"{user_number} {task.order_number}\n"
        for link, message in results.items():
            result_string += f"<a href='{link}'>Ссылка</a>:\n{message}\n"

        check_kb = KeyboardCreator().create_check_keyboard()
        bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=result_string,
            disable_web_page_preview=True,
            reply_markup=check_kb,
            parse_mode='HTML'
        )

    else:
        return task


def process_advanced_chat(user, callback, task, bot):
    processor = ChatProcessor(user, callback, task, bot)
    return processor.process()
