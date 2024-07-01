from channels.db import database_sync_to_async

from core.bot.models import Chat, BotUser, LinksQueue, VIPCode, TaskStorage


class DatabaseManager:
    @staticmethod
    @database_sync_to_async
    def get_chat_settings(message_chat):
        return Chat.objects.get(bot_chats=f'https://t.me/{message_chat}')

    @staticmethod
    @database_sync_to_async
    def create_tg_user(**kwargs):
        return BotUser.objects.update_or_create(defaults=kwargs, **kwargs)

    @staticmethod
    @database_sync_to_async
    def create_link(**kwargs):
        return LinkStorage.objects.update_or_create(defaults=kwargs, **kwargs)

    @staticmethod
    @database_sync_to_async
    def create_link_queue(**kwargs):
        return LinksQueue.objects.create(**kwargs)

    @staticmethod
    @database_sync_to_async
    def create_task_storage(**kwargs):
        return TaskStorage.objects.get_or_create(**kwargs)

    @staticmethod
    @database_sync_to_async
    def create_done_list(**kwargs):
        return UserDoneLinks.objects.create(**kwargs)

    @staticmethod
    @database_sync_to_async
    def get_vip_code():
        return VIPCode.objects.all()

