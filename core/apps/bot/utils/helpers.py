import re

from channels.db import database_sync_to_async
from telebot import types

from core.apps.bot.constants.bot_label import BotLabel
from core.apps.bot.constants.users_type import UserTypes
from core.apps.bot.models import Chat, LinkStorage, TaskStorage


async def get_chat(message: types.Message) -> Chat:
    """
    Получает чат
    """
    chat = await database_sync_to_async(Chat.objects.get)(bot_chats=f'https://t.me/{message.chat.username}')
    chat_id = message.chat.id

    if chat.chat_id != chat_id:
        chat.chat_id = chat_id
        await database_sync_to_async(chat.save)(update_fields=['chat_id'])

    return chat


async def check_message(message: types.Message) -> dict:
    """
    Проверяет корректность отправленной ссылки с комментарием или без
    """
    result = {
        'link': None,
        'comment': None,
        'error': None
    }

    if not message.entities or message.entities[0].type != 'url':
        result['error'] = "Некорректный формат ссылки"
        return result

    link_count = message.text.count('vk.com')
    if link_count != 1:
        result['error'] = "Можно отправить только одну ссылку за раз"
        return result

    vk_link = message.text
    match = re.search(r'wall-\d+_\d+', vk_link)
    if match:
        if match:
            wall_id = match.group(0)
            rest_of_link = vk_link[match.end():]
            result['link'] = f"https://vk.com/{wall_id}"
            result['comment'] = rest_of_link if rest_of_link else None
    else:
        result['error'] = "Ссылка не соответствует формату VK"

    return result


async def check_recent_objects(user, chat):
    allow_link_count = chat.reply_link_count

    exists = await database_sync_to_async(
        lambda: LinkStorage.objects.filter(chat_type=BotLabel(chat.chat_label).name, bot_user=user.id).exists()
    )()

    if exists:

        links_allow_qs = await database_sync_to_async(
            lambda: list(LinkStorage.objects.filter(chat_type=BotLabel(chat.chat_label).name)
                         .order_by("-added_at")[:allow_link_count])
        )()

        links_storage = [link for link in links_allow_qs if link.bot_user_id != user.id]
        links_length = len(links_storage)
        total_links = allow_link_count - links_length
        if total_links > allow_link_count:
            total_links = 0
            return total_links
        else:
            return total_links

    else:
        total_links = 0
        return total_links


async def check_current_task(user, chat):
    if user.status == UserTypes.VIP:
        pass
    else:
        chat_name = chat.bot_chats.split('/')[-1]

        ts_qs = await database_sync_to_async(TaskStorage.objects.filter)(
            bot_user=user.id,
            chat_task=chat_name,
            task_completed=False
        )
        ts_last = await database_sync_to_async(ts_qs.last)()

        if ts_last:
            return ts_last
