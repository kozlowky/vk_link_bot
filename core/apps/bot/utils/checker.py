import string
import re

import requests
from channels.db import database_sync_to_async
from vk_api import ApiError

from core.apps.bot.constants.bot_label import BotLabel
from core.apps.bot.models import Chat


class VkChecker:
    def __init__(self, vk, bot):
        self.vk = vk
        self.bot = bot

    @staticmethod
    async def get_owner_and_post_ids(link):
        match_post = re.search(r'wall(-)?(\d+_\d+)', link)
        if match_post:
            has_prefix, match = match_post.groups()
            owner_id_match = re.search(r'(\d+)_\d+', match)
            owner_id = "-" + owner_id_match.group(1) if has_prefix else owner_id_match.group(1)
            post_id_match = re.search(r'\d+_(\d+)', match)
            post_id = post_id_match.group(1)
            return owner_id, post_id

    async def get_likes(self, link, owner_id, post_id, user_id):
        likes = self.vk.likes.getList(
            type='post',
            owner_id=owner_id,
            item_id=post_id,
            filter='likes',
            extended=1
        )
        user_likes = [user['id'] for user in likes['items']]
        vk_id = user_id.vk_id
        return vk_id in user_likes

    async def get_vk_comment(self, owner_id, post_id, vk_id):
        comments = self.vk.wall.getComments(
                        type='post',
                        owner_id=int(owner_id),
                        post_id=int(post_id),
                        extended=1
                    )
        user_comments = []

        if 'items' in comments and comments['items']:
            for comment in comments['items']:
                if 'from_id' in comment and comment['from_id'] == vk_id:
                    user_comments.append(comment)
        try:
            comment_string = user_comments[0].get('text')
            translator = str.maketrans("", "", string.punctuation)
            comment = comment_string.translate(translator)

            words = comment.split()
            user_comment_length = len(words)
        except IndexError:
            user_comment_length = 0

        return user_comment_length

    async def get_subscriptions(self, owner_id, vk_id):
        owner_id = int(owner_id[1:])
        subs_dict = self.vk.users.getSubscriptions(
            type='post',
            user_id=vk_id
        )
        subs = subs_dict.get('groups').get('items')
        if owner_id in subs:
            return True

    async def get_chat_type(self, callback):
        pattern = r'из группы (\S+):'
        match = re.search(pattern, callback.text)
        chat_id = match.group(1)
        chat_settings = await database_sync_to_async(Chat.objects.get)(
            bot_chats=f'https://t.me/{chat_id}')
        chat_type = chat_settings.chat_label
        return chat_type

    async def get_user_id(self, vk_page_url):
        try:
            response = requests.get(vk_page_url)
            response.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            return f"Ошибка HTTP: {errh}"

        vk_id = vk_page_url.split('/')[-1]

        if not vk_id.replace('id', '').isdigit():
            try:
                vk_user_info = self.vk.utils.resolveScreenName(screen_name=vk_id)
                vk_id = vk_user_info['object_id']
            except ApiError as e:
                return f'Ошибка при получении id пользователя: {e}'
        else:
            vk_id = vk_id.replace('id', '')

        try:
            vk_id = int(vk_id)
        except ValueError:
            return "Невозможно извлечь ID пользователя."

        return vk_id

    async def get_task_code(self, message):
        task_code = None
        match = re.search(r's*([a-fA-F0-9]+)', message)
        if match:
            task_code = match.group(1)
        return task_code

    async def run_advanced_chat(self, callback, user_id):
        vk_id = user_id.vk_id
        # chat_type = await self.get_chat_type(callback)

        links = re.findall(r'(https:\/\/vk\.com\/\S+)', callback.text)
        result = []
        for link in links:
            owner_id, post_id = await self.get_owner_and_post_ids(link)
            check_likes = await self.get_likes(link, owner_id, post_id, user_id)
            get_comment = await self.get_vk_comment(owner_id, post_id, vk_id)
            get_subs = await self.get_subscriptions(owner_id, vk_id)
            data = {
                'link': link,
                'likes': check_likes,
                'commnet': get_comment,
                'sub': get_subs,
            }
            result.append(data)

        return result

    async def run_default_chat(self, callback, user_id):
        links = re.findall(r'(https:\/\/vk\.com\/\S+)', callback.text)
        result = []
        for link in links:
            owner_id, post_id = await self.get_owner_and_post_ids(link)
            check_likes = await self.get_likes(link, owner_id, post_id, user_id)

            data = {
                'link': link,
                'likes': check_likes,
            }

            result.append(data)
        return result


