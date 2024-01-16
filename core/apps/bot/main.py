import asyncio
import logging
from urllib.parse import urlparse

import requests
import re

import telebot
from telebot import types
from telebot.async_telebot import AsyncTeleBot

import vk_api

from channels.db import database_sync_to_async

from django.conf import settings
from vk_api import ApiError

from core.apps.bot.kb import KeyboardCreator
from core.apps.bot.models import BotUser, VKUser

bot = AsyncTeleBot(settings.TOKEN_BOT, parse_mode='HTML')
telebot.logger.setLevel(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)
keyboard_creator = KeyboardCreator()

vk_session = vk_api.VkApi(token=settings.VK_ACCESS_TOKEN)
vk = vk_session.get_api()

mute_users = set()
users_vk = []


test_links = [
    'https://vk.com/it_joke?w=wall-46453123_363333',
    'https://vk.com/it_joke?w=wall-46453123_363284',
    'https://vk.com/it_joke?w=wall-46453123_363267',
    'https://vk.com/it_joke?w=wall-46453123_363249'
]

@database_sync_to_async
def create_tg_user(user_id, first_name, last_name, username):
    return BotUser.objects.create(
        tg_id=user_id,
        first_name=first_name,
        last_name=last_name,
        username=username,
    )


@database_sync_to_async
def create_vk_user(vk_id, vk_page_url):
    if vk_id:
        return VKUser.objects.create(
            vk_id=vk_id,
            vk_page_url=vk_page_url,
        )
    return None


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
        await create_tg_user(user_id, first_name, last_name, username)
    await bot.reply_to(message, "Для регистрации отправьте ссылку на страницу ВК")


@bot.message_handler(func=lambda message: message.chat.type in ['private'])
async def process_vk_id(message):
    a = message.chat.type
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
        await database_sync_to_async(VKUser.objects.get)(vk_id=vk_id)
        await bot.send_message(message.chat.id, f"Пользователь уже существует", reply_markup=kb)
    except VKUser.DoesNotExist:
        vk_user = await create_vk_user(vk_id, vk_page_url)
        if vk_user:
            user_tg.vk_user = vk_user
            await database_sync_to_async(user_tg.save)()
        await bot.send_message(message.chat.id, "Регистрация прошла успешно!", reply_markup=kb)


@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'])
async def chat_member_handler(message: types.Message):
    user_id = message.from_user.id
    try:
        chat_user = await database_sync_to_async(BotUser.objects.get)(tg_id=message.from_user.id)
        if chat_user:
            if message.entities and message.entities[0].type == 'url':
                if 'wall' in message.text:
                    check_kb = keyboard_creator.create_check_keyboard()
                    user_chat_id = message.from_user.id
                    await bot.send_message(user_chat_id,
                                           f"Ваше задание:\n {test_links}",
                                           disable_web_page_preview=True,
                                           reply_markup=check_kb)
    except BotUser.DoesNotExist:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            until_date=0,
            can_send_messages=False
        )


@bot.callback_query_handler(func=lambda callback: callback.data == 'check_button')
async def check_task(callback: types.CallbackQuery):
    if callback.data == 'check_button':
        print(callback.message.text)

        links = re.findall(r'(https:\/\/vk\.com\/\S+)', callback.message.text)
        print(links)

        if links:
            posts_without_like = []

            for post_link in test_links:
                print("Checking post link:", post_link)

                match_post = re.search(r'wall-(\d+)_', post_link)
                if match_post:
                    owner_id = "-" + match_post.group(1)
                    post_id_match = re.search(r'wall-\d+_(\d+)', post_link)
                    post_id = post_id_match.group(1)

                    likes = vk.likes.getList(
                        type='post',
                        owner_id=owner_id,
                        item_id=post_id,
                        filter='likes',
                        extended=1
                    )

                    user_likes = [user['id'] for user in likes['items']]
                    user_id = await database_sync_to_async(BotUser.objects.get)(tg_id=callback.from_user.id)
                    vk_user = await database_sync_to_async(lambda: user_id.vk_user)()
                    vk_id = vk_user.vk_id
                    if vk_id not in user_likes:
                        posts_without_like.append(post_link)

                else:
                    print("Ошибка при извлечении ID поста.")

            if posts_without_like:
                print(posts_without_like)
                message = "Вы не поставили лайк в следующих постах:\n" + "\n".join(posts_without_like)
            else:
                message = 'Задание принято!'

            check_kb = keyboard_creator.create_check_keyboard()
            await bot.edit_message_text(chat_id=callback.message.chat.id,
                                        message_id=callback.message.message_id,
                                        text=message,
                                        disable_web_page_preview=True,
                                        reply_markup=check_kb)
        else:
            print("Ссылок не найдено.")
