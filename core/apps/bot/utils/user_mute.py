from channels.db import database_sync_to_async
from core.apps.bot.models import BotSettings


class UserHandler:
    def __init__(self, bot):
        self.bot = bot

    async def mute_user(self, message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        user_get = await self.bot.get_chat_member(chat_id, user_id)
        user_status = user_get.status if user_get else None

        if user_status not in ['administrator', 'creator']:
            await self.bot.restrict_chat_member(chat_id, user_id, until_date=0)

    async def unmute_user(self, callback, user_id):
        chat_settings = await database_sync_to_async(BotSettings.objects.get)()
        chat_id = chat_settings.chat_id
        await self.bot.restrict_chat_member(chat_id, user_id.tg_id,
                                            can_send_messages=True,
                                            can_send_media_messages=True,
                                            can_send_other_messages=True,
                                            can_add_web_page_previews=True)