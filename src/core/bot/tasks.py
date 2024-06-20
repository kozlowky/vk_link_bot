import logging
from django.utils import timezone
from celery import shared_task
from core.bot.models import BotUser
from core.bot.constants.users_type import UserTypes
from core import celery_app

logger = logging.getLogger(__name__)


@shared_task(name="say_hello")
def say_hello():
    logging.info('info hello')
    logging.warning('warning hello')
    logging.error('error hello')


@celery_app.task()
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
