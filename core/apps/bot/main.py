import asyncio
import logging

import telebot
from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
from telebot.asyncio_handler_backends import State, StatesGroup

import vk_api

from channels.db import database_sync_to_async

from django.conf import settings
from vk_api import ApiError

from core.apps.bot.kb import KeyboardCreator
from core.apps.bot.models import BotUser, LinkStorage, LinksQueue, UserDoneLinks, BotSettings
from core.apps.bot.utils.checker import VkChecker
from core.apps.bot.utils.db_handler import DatabaseManager
from core.apps.bot.utils.user_mute import UserHandler

state_storage = StateMemoryStorage()
bot = AsyncTeleBot(settings.TOKEN_BOT, parse_mode='HTML', state_storage=state_storage)
telebot.logger.setLevel(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)
keyboard_creator = KeyboardCreator()

vk_session = vk_api.VkApi(token=settings.VK_ACCESS_TOKEN)
vk = vk_session.get_api()

user_handler = UserHandler(bot)
db_manager = DatabaseManager()


class MyStates(StatesGroup):
    chat_type = State()


@bot.message_handler(commands=['start'])
async def send_welcome(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.username

    await asyncio.sleep(1)
    try:
        await database_sync_to_async(BotUser.objects.get)(tg_id=user_id)
    except BotUser.DoesNotExist:
        await db_manager.create_tg_user(tg_id=user_id,
                             first_name=first_name,
                             last_name=last_name,
                             username=username)

    await bot.reply_to(message, "Для регистрации отправьте ссылку на страницу ВК")


@bot.message_handler(func=lambda message: message.chat.type in ['private'])
async def process_vk_id(message):
    try:
        user_tg = await database_sync_to_async(BotUser.objects.get)(tg_id=message.from_user.id)
    except BotUser.DoesNotExist:
        await bot.send_message(message.chat.id, "Пользователь не найден. Введите /start для начала.")
        return

    if not message.entities or message.entities[0].type != 'url':
        await bot.send_message(message.chat.id, "Пожалуйста, введите корректный URL.")
        return

    vk_page_url = message.text
    vk_id = None
    if 'vk.com/' in vk_page_url:
        vk_id = vk_page_url.split('/')[-1]

    if not vk_id.replace('id', '').isdigit():
        try:
            vk_user_info = vk.utils.resolveScreenName(screen_name=vk_id)
            vk_id = vk_user_info['object_id']
        except ApiError as e:
            await bot.send_message(message.chat.id, f"Ошибка при получении id пользователя: {e}")
            return
    else:
        vk_id = vk_id.replace('id', '')
    vk_id = int(vk_id)
    kb = keyboard_creator.create_admin_keyboard() if user_tg.is_admin else keyboard_creator.create_user_keyboard()

    try:
        await database_sync_to_async(BotUser.objects.get)(vk_id=vk_id)
        await bot.send_message(message.chat.id, f"Пользователь уже существует", reply_markup=kb)
    except BotUser.DoesNotExist:
        user_tg.vk_id = vk_id
        user_tg.vk_user_url = vk_page_url
        await database_sync_to_async(user_tg.save)()
        await bot.send_message(message.chat.id, "Регистрация прошла успешно!", reply_markup=kb)


@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'])
async def chat_member_handler(message: types.Message):
    user_id = message.from_user.id
    message_chat = message.chat.username
    try:
        chat = await db_manager.get_chat_settings(message_chat)

        if chat:
            chat_id = message.chat.id
            chat.chat_id = chat_id
            await database_sync_to_async(chat.save)()
            try:
                chat_user = await database_sync_to_async(BotUser.objects.get)(tg_id=message.from_user.id)
                if chat_user:
                    if message.entities and message.entities[0].type == 'url':
                        if 'wall' in message.text:
                            vk_link = message.text
                            await db_manager.create_link(bot_user=chat_user, vk_link=vk_link)
                            check_kb = keyboard_creator.create_check_keyboard()
                            tasks_qs = await database_sync_to_async(
                                lambda: list(LinksQueue.objects.exclude(bot_user_id=chat_user.id).values()))()
                            done_qs = await database_sync_to_async(UserDoneLinks.objects.filter)(bot_user=chat_user)
                            done_ids = set(await database_sync_to_async(lambda: {q.link_id for q in done_qs})())
                            user_tasks = [task['vk_link'] for task in tasks_qs if task['id'] not in done_ids]

                            if user_tasks:
                                await user_handler.mute_user(message)
                                message_text = f"Ваше задание из группы {message_chat}:\n" + '\n'.join(user_tasks)
                                await bot.send_message(user_id,
                                                       message_text,
                                                       disable_web_page_preview=True,
                                                       reply_markup=check_kb)
                            else:
                                await bot.send_message(user_id, "Нет заданий")

            except BotUser.DoesNotExist:
                await bot.restrict_chat_member(
                    chat_id=message.chat.id,
                    user_id=user_id,
                    until_date=0,
                    can_send_messages=False
                )
    except BotSettings.DoesNotExist:
        user_id = message.from_user.id
        exist_chat = message.chat.username
        await bot.send_message(user_id, f"Меня пытаються добавить в группу https://t.me/{exist_chat}")


@bot.callback_query_handler(func=lambda callback: callback.data == 'check_button')
async def check_task(callback: types.CallbackQuery):
    if callback.data == 'check_button':
        user_id = await database_sync_to_async(BotUser.objects.get)(tg_id=callback.from_user.id)
        check = VkChecker(vk, bot)
        data = await check.run(callback.message, user_id)

        posts_without_like = []
        for item in data:
            link = item.get('link')
            likes = item.get('likes')

            if not likes:
                posts_without_like.append(link)

            tasks_qs = await database_sync_to_async(lambda: list(LinksQueue.objects.all().values()))()
            for task in tasks_qs:
                if task['vk_link'] == link and link not in posts_without_like:
                    task_instance = await database_sync_to_async(LinksQueue.objects.get)(id=task['id'])
                    await database_sync_to_async(UserDoneLinks.objects.get_or_create)(
                        bot_user=user_id,
                        link=task_instance
                    )

        if posts_without_like:
            message = "Вы не поставили лайк в следующих постах:\n" + "\n".join(posts_without_like)
            check_kb = keyboard_creator.create_check_keyboard()
            await bot.edit_message_text(chat_id=callback.message.chat.id,
                                        message_id=callback.message.message_id,
                                        text=message,
                                        disable_web_page_preview=True,
                                        reply_markup=check_kb)
        else:
            message = 'Задание принято!'
            links_qs = await database_sync_to_async(lambda: LinkStorage.objects.filter(
                bot_user=user_id).last())()
            vk_link = links_qs.vk_link
            links_qs.is_approved = True
            await database_sync_to_async(links_qs.save)()
            await db_manager.create_link_queue(bot_user=user_id, vk_link=vk_link)
            await bot.edit_message_text(chat_id=callback.message.chat.id,
                                        message_id=callback.message.message_id,
                                        text=message,
                                        disable_web_page_preview=True
                                        )
            await user_handler.unmute_user(callback, user_id)
