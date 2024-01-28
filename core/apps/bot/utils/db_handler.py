from channels.db import database_sync_to_async

from core.apps.bot.models import BotSettings, BotUser, LinkStorage, LinksQueue, UserDoneLinks


class DatabaseManager:
    @staticmethod
    @database_sync_to_async
    def get_chat_settings(message_chat):
        return BotSettings.objects.get(bot_chats=f'https://t.me/{message_chat}')

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
        return LinksQueue.objects.update_or_create(defaults=kwargs, **kwargs)

    @staticmethod
    @database_sync_to_async
    def create_done_list(**kwargs):
        return UserDoneLinks.objects.update_or_create(defaults=kwargs, **kwargs)

