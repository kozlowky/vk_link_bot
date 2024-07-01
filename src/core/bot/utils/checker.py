import re
import string

import requests
from vk_api import ApiError

from core.bot.models import Chat


class VkChecker:
    """ Класс для проверки различных аспектов ВКонтакте. """

    def __init__(self, vk):
        self.vk = vk

    @staticmethod
    def get_owner_and_post_ids(link):
        """ Получает из ссылки owner_id и post_id """

        rest_of_link = link.split("wall")[1]
        parts = rest_of_link.split("_")
        owner_id = parts[0]
        post_id = parts[1]
        return owner_id, post_id

    def get_likes(self, owner_id, post_id, user_id):
        """ Получает лайки из поста ВК """

        likes = self.vk.likes.getList(
            type='post',
            owner_id=owner_id,
            item_id=post_id,
            filter='likes',
            extended=1,
            count=1000,
        )
        user_likes = [user['id'] for user in likes['items']]
        vk_id = user_id.vk_id
        return vk_id in user_likes

    def get_vk_comment(self, owner_id, post_id, vk_id):
        """ Получает комментарии из поста ВК """

        comments = self.vk.wall.getComments(
            type='post',
            owner_id=owner_id,
            post_id=post_id,
            extended=1,
            sort='desc',
        )
        user_comments = []

        if 'items' in comments and comments['items']:
            for comment in comments['items']:
                if 'from_id' in comment and comment['from_id'] == vk_id:
                    user_comments.append(comment)

        if user_comments:
            comment_string = user_comments[0].get('text')
            translator = str.maketrans("", "", string.punctuation)
            comment = comment_string.translate(translator)
            words = comment.split()
            user_comment_length = len(words)
            # TODO Значение длины комментария задаем в настройках БОТА !!!
            if user_comment_length >= 5:
                return True

        return False


    def get_subscriptions(self, owner_id, vk_id):
        """ Проверяет подписан ли пользователь на страницу ВК """

        abs_owner_id = abs(owner_id)
        subs_dict = self.vk.users.getSubscriptions(
            extended=1,
            user_id=vk_id
        )
        subs = [
            abs(item['id']) for item in subs_dict.get(
                'items', []
            ) if isinstance(item, dict) and 'id' in item
        ]

        if abs_owner_id in subs:
            return True
        return False

    # TODO Не нужный метод
    def get_chat_type(self, callback):
        """ Получает тип чата """

        pattern = r'из группы (\S+):'
        match = re.search(pattern, callback.text)
        chat_id = match.group(1)
        chat_settings = Chat.objects.get(
            bot_chats=f'https://t.me/{chat_id}'
        )
        chat_type = chat_settings.chat_label
        return chat_type

    def get_user_id(self, vk_page_url):
        """ Получает идентификатор пользователя ВКонтакте из URL его страницы. """

        try:
            response = requests.get(vk_page_url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            return None

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

    def get_task_code(self, message):
        """ Получпет код задания из сообщения """

        task_code = None
        match = re.search(r's*([a-fA-F0-9]+)', message)
        if match:
            task_code = match.group(1)
        return task_code

    def run_advanced_chat(self, task, user):
        """ Запускает проверку для чата с типом ADVANCED """

        vk_id = user.vk_id
        links = task.links.all()
        result = []
        for link in links:
            like = self.get_likes(link.owner_id, link.post_id, user)
            comment = self.get_vk_comment(link.owner_id, link.post_id, vk_id)
            subs = self.get_subscriptions(link.owner_id, vk_id)
            data = {
                link.vk_link: {
                    'likes': like,
                    'comment': comment,
                    'sub': subs,
                }
            }
            result.append(data)

        return result

    def run_default_chat(self, task, user):
        """ Запускает проверку для чата с типом DEFAULT """

        links = task.links.all()
        result = []
        for link in links:
            like = self.get_likes(link.owner_id, link.post_id, user)

            data = {
                link.vk_link: {
                    'likes': like,
                }
            }
            result.append(data)

        return result
        # links = re.findall(r'(https:\/\/vk\.com\/\S+)', callback.text)
        # result = []
        # for link in links:
        #     owner_id, post_id = self.get_owner_and_post_ids(link)
        #     check_likes = self.get_likes(owner_id, post_id, user_id)
        #
        #     data = {
        #         'link': link,
        #         'likes': check_likes,
        #     }
        #
        #     result.append(data)
        # return result
