from core.apps.bot.constants.state_type import StateTypes
from core.apps.bot.models import BotUser
from channels.db import database_sync_to_async


@database_sync_to_async
def get_user_state(user):
    try:
        # user = BotUser.objects.get(tg_id=tg_id)
        return user.state_menu
    except BotUser.DoesNotExist:
        return None


@database_sync_to_async
def set_user_state(user, state):
    try:
        # user = BotUser.objects.get(tg_id=tg_id)
        user.state_menu = state
        user.save()
        return True
    except BotUser.DoesNotExist:
        return False


@database_sync_to_async
def reset_user_state(user):
    try:
        # user = BotUser.objects.get(tg_id=tg_id)
        user.state_menu = StateTypes.DEFAULT.value
        user.save()
        return True
    except BotUser.DoesNotExist:
        return False
