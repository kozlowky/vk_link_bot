import logging

from django.conf import settings
from django.utils import timezone
from celery import shared_task
from vk_api import vk_api

from core.bot.handlers.chats import ChatMemberHandler
from core.bot.models import BotUser, Chat, MessageText
from core.bot.constants.users_type import UserTypes
from core.bot.utils.checker import VkChecker

logger = logging.getLogger(__name__)

vk = vk_api.VkApi(token=settings.VK_ACCESS_TOKEN).get_api()
checker_instance = VkChecker(vk)


@shared_task(name="say_hello")
def say_hello():
    logging.info('info hello')
    logging.warning('warning hello')
    logging.error('error hello')


@shared_task(name="check_vip_status")
def update_vip_status():
    logger.info("Starting update_vip_status task...")

    users = BotUser.objects.filter(status=UserTypes.VIP)
    for user in users:
        if user.vip_end_date < timezone.now().date():
            logger.info("Updating VIP status for user %s", user.id)
            user.status = 0
            user.vip_end_date = None
            user.vip_code_id = None
            user.save()

    logger.info("update_vip_status task completed.")


@shared_task
def handle_message_task(message):
    try:
        logger.info("Start task")
        user_id = message["from"]["id"]
        chat_id = message["chat"]["id"]

        user = BotUser.objects.filter(tg_id=user_id).first()
        chat = Chat.objects.filter(chat_id=chat_id).first()

        handler = ChatMemberHandler(chat, user)
        response = handler.handle_message(message)
        return response

    except Exception as e:
        return f"ЧТО-ТО ПОШЛО НЕ ТАК ОБРАТИТЕСЬ К АДМИНИСТРАТОРУ, ОШИБКА: <b>{e}</b>"

