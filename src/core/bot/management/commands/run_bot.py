import logging

from django.conf import settings
from django.core.management import BaseCommand
from telebot import util
from core.bot.main import bot

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Запуск Телеграмм бота
    """
    help = "Run Telegram Bot"

    def handle(self, *args, **options):
        try:
            bot.infinity_polling(logger_level=settings.LOG_LEVEL, allowed_updates=util.update_types)
        except Exception as e:
            logger.error('Error: %s', e)
