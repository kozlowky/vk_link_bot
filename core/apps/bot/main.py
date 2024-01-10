import asyncio
import logging
import requests
import re

import telebot
from telebot import types
from telebot.async_telebot import AsyncTeleBot

import vk_api

from channels.db import database_sync_to_async

from django.conf import settings
from core.apps.bot.kb import KeyboardCreator
from core.apps.bot.models import User

bot = AsyncTeleBot(settings.TOKEN_BOT, parse_mode='HTML')
vk_token = settings.VK_ACCESS_TOKEN
telebot.logger.setLevel(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)
keyboard_creator = KeyboardCreator()

mute_users = set()
user_states = {}
users_vk = []

links = [
    "https://vk.com/it_joke?w=wall-46453123_358613",
    "https://vk.com/it_joke?w=wall-46453123_362979",
    "https://vk.com/rhymes?w=wall-28905875_33066235"
]


@database_sync_to_async
def create_user(user_id, first_name, last_name, username):
    return User.objects.create(
        tg_id=user_id,
        first_name=first_name,
        last_name=last_name,
        username=username
    )


@bot.message_handler(commands=['start'])
async def send_welcome(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.full_name

    await asyncio.sleep(1)

    await create_user(user_id, first_name, last_name, username)

    user_keyboard = keyboard_creator.create_admin_keyboard()
    await bot.reply_to(message, "Для продолжения нажмите на кнопку 'Указать VK ID'", reply_markup=user_keyboard)
    await bot.send_message(message.chat.id, message.chat.id)


@bot.message_handler(func=lambda message: message.text == "Указать VK ID")
async def get_user_id(message):
    markup = types.ForceReply(selective=False)
    await bot.send_message(message.chat.id, "Введите ваш VK ID:", reply_markup=markup)
    user_states[message.chat.id] = "waiting_for_vk_id"


@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "waiting_for_vk_id")
async def process_vk_id(message):
    user_vk_id = message.text
    print("Received VK ID:", user_vk_id)
    user_states[message.chat.id] = None
    await bot.send_message(message.chat.id, "Спасибо за предоставленный VK ID!")
    users_vk.append(user_vk_id)


@bot.message_handler(func=lambda message: True)
async def handle_message(message):
    check_kb = keyboard_creator.create_check_keyboard()
    user_id = message.from_user.id
    chat_id = message.chat.id

    if message.entities and message.entities[0].type == 'url':
        if 'w=wall' in message.text:
            message_text = "Здесь ваше задание:\n" + "\n".join(links)
            # mute_users.add(user_id)
            # await bot.restrict_chat_member(chat_id, user_id, can_send_messages=False)
            await bot.send_message(user_id, message_text, disable_web_page_preview=True, reply_markup=check_kb)
        else:
            await bot.reply_to(message, 'Некорректная ссылка')
    else:
        await bot.reply_to(message, 'Сообщение не содержит ссылки.')


@bot.callback_query_handler(func=lambda callback: callback.data == 'check_button')
async def check_task(callback: types.CallbackQuery):
    if callback.data == 'check_button':
        print(callback.message.text)

        links = re.findall(r'(https:\/\/vk\.com\/\S+)', callback.message.text)
        print(links)

        if links:
            posts_without_like = []

            for post_link in links:
                print("Extracted post link:", post_link)

                match_post = re.search(r'wall-(\d+)_', post_link)
                if match_post:
                    owner_id = "-" + match_post.group(1)
                    print("Extracted owner_id:", owner_id)
                    post_id_match = re.search(r'wall-\d+_(\d+)', post_link)
                    post_id = post_id_match.group(1)
                    print("Extracted post_id:", post_id)

                    vk_session = vk_api.VkApi(token=settings.VK_ACCESS_TOKEN)

                    vk = vk_session.get_api()

                    likes = vk.likes.getList(
                        type='post',
                        owner_id=owner_id,
                        item_id=post_id,
                        filter='likes',
                        extended=1
                    )

                    user_id = int(users_vk[0])
                    print(users_vk)
                    user_likes = [user['id'] for user in likes['items']]
                    print(user_likes)
                    if user_id in user_likes:
                        print(f"User {callback.from_user.first_name} {callback.from_user.last_name} ({user_id}) поставил лайк.")
                        links.remove(post_link)
                    else:
                        print(f"User {callback.from_user.first_name} {callback.from_user.last_name} ({user_id}) не поставил лайк.")
                        posts_without_like.append(post_link)

                else:
                    print("Ошибка при извлечении ID поста.")

            if posts_without_like:
                message = "Вы не поставили лайк в следующих постах:\n" + "\n".join(posts_without_like)
                await bot.send_message(callback.message.chat.id, message)
            else:
                await bot.send_message(callback.message.chat.id, 'Вы поставили лайк во всех указанных постах. ОК')

        else:
            print("Ссылок не найдено.")

        await bot.send_message(callback.message.chat.id, 'Ok')




# @bot.message_handler(func=lambda message: True)
# async def echo_message(message):
#     user_id = message.from_user.id
#     task_text = "Здесь ваше задание..."
#     await bot.send_message(user_id, task_text)
#     await bot.send_message(user_id, message.text)



# # Создайте экземпляр VK API
# vk_session = vk_api.VkApi(token=settings.VK_ACCESS_TOKEN)
#
# # Получите API
# vk = vk_session.get_api()
#
# # Укажите ID пользователя (в данном случае, для группы it_joke)
# owner_id = -46453123  # ID группы it_joke
#
# # Получите информацию о стене группы (первый пост)
# wall_info = vk.wall.get(owner_id=owner_id, count=1)
#
# # Проверка, что есть посты
# if wall_info['items']:
#     # Получите ID первого поста
#     post_id = wall_info['items'][0]['id']
#
#     # Получите список пользователей, поставивших лайк
#     likes = vk.likes.getList(
#         type='post',
#         owner_id=owner_id,
#         item_id=post_id,
#         filter='likes',
#         extended=1
#     )
#
#     # Выведите список пользователей, поставивших лайк
#     for user in likes['items']:
#         print(user['first_name'], user['last_name'], user['id'])
# else:
#     print("На стене нет постов.")