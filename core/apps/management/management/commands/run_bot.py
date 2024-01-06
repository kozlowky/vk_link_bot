import asyncio
from django.core.management.base import BaseCommand, CommandError

from core.apps.bot.main import bot


class Command(BaseCommand):
    help = "Run Telegram Bot"

    def handle(self, *args, **options):
        asyncio.run(bot.polling())
