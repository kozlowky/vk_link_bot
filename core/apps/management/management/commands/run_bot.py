import asyncio
import logging

from django.core.management.base import BaseCommand
from django.conf import settings
from telebot import util

from core.apps.bot.main import bot

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run Telegram Bot"

    def handle(self, *args, **options):
        try:
            asyncio.run(bot.infinity_polling(logger_level=settings.LOG_LEVEL, allowed_updates=util.update_types))
        except Exception as e:
            logger.error(f'Error: {e}')
