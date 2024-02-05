import logging
import uuid
from datetime import timedelta

import telebot
from django.utils import timezone
from telebot import types
from telebot.async_telebot import AsyncTeleBot

import vk_api

from channels.db import database_sync_to_async

from django.conf import settings

from core.apps.bot.constants import message_text
from core.apps.bot.constants import chat_types
from core.apps.bot.constants.state_type import StateTypes
from core.apps.bot.constants.users_type import UserTypes
from core.apps.bot.kb import KeyboardCreator, user_kb_list, admin_kb_list, start_menu_kb
from core.apps.bot.models import BotUser, LinkStorage, LinksQueue, UserDoneLinks, BotSettings, VIPCode, TaskStorage
from core.apps.bot.utils import state_worker, checker
from core.apps.bot.utils.db_handler import DatabaseManager
from core.apps.bot.utils.user_mute import UserHandler

bot = AsyncTeleBot(settings.TOKEN_BOT, parse_mode='HTML')
telebot.logger.setLevel(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)
keyboard_creator = KeyboardCreator()

vk_session = vk_api.VkApi(token=settings.VK_ACCESS_TOKEN)
vk = vk_session.get_api()

user_handler = UserHandler(bot)
db_manager = DatabaseManager()
checker_instance = checker.VkChecker(vk, bot)


@bot.message_handler(commands=['start'], func=lambda message: message.chat.type == chat_types.PRIVATE_CHAT_TYPE)
async def send_welcome(message):
    user_id = message.from_user.id
    try:
        user = await database_sync_to_async(BotUser.objects.get)(tg_id=message.from_user.id)
        await state_worker.reset_user_state(user)
        if user.is_admin:
            kb = keyboard_creator.create_admin_keyboard()
        else:
            kb = keyboard_creator.create_user_keyboard()
        await bot.reply_to(message, text=message_text.auth_user, reply_markup=kb)
    except BotUser.DoesNotExist:
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        username = message.from_user.username
        await db_manager.create_tg_user(tg_id=user_id,
                                        first_name=first_name,
                                        last_name=last_name,
                                        username=username)
        kb = keyboard_creator.create_start_keyboard()
        await bot.reply_to(message, text=message_text.start_message, reply_markup=kb)


@bot.message_handler(
    func=lambda message: message.text in start_menu_kb and message.chat.type == chat_types.PRIVATE_CHAT_TYPE)
async def vip_choices(message):
    user = await database_sync_to_async(BotUser.objects.get)(tg_id=message.from_user.id)
    if message.text == "Есть":
        await bot.send_message(message.chat.id,
                               text=message_text.vip_code_enter)
        await state_worker.set_user_state(user, state=StateTypes.VIP_CODE)

    else:
        if user.is_admin:
            kb = keyboard_creator.create_admin_keyboard()
        else:
            kb = keyboard_creator.create_user_keyboard()
        await bot.reply_to(message, text=message_text.link_enter, reply_markup=kb)


@bot.message_handler(func=lambda message: message.text in (
        user_kb_list + admin_kb_list) and message.chat.type == chat_types.PRIVATE_CHAT_TYPE)
async def handle_menu(message):
    user = await database_sync_to_async(BotUser.objects.get)(tg_id=message.from_user.id)
    if message.text == "Указать VK ID":
        await state_worker.set_user_state(user, state=StateTypes.VK_LINK)
        await bot.send_message(message.chat.id,
                               text=message_text.link_enter)
    elif message.text == "Ввести ВИП код":
        await state_worker.set_user_state(user, state=StateTypes.VIP_CODE)
        await bot.send_message(message.chat.id,
                               text=message_text.vip_code_enter)
    elif message.text == "Получить статус пользователя":
        await state_worker.set_user_state(user, state=StateTypes.GET_STATUS)
        await get_status(message, user)


@bot.message_handler(func=lambda message: True and message.chat.type == chat_types.PRIVATE_CHAT_TYPE,
                     content_types=['text'])
async def handle_text_message(message):
    user = await database_sync_to_async(BotUser.objects.get)(tg_id=message.from_user.id)
    current_state = await state_worker.get_user_state(user)
    if current_state == StateTypes.VK_LINK:
        await check_link(message, user)
    elif current_state == StateTypes.VIP_CODE:
        await get_vip_code(message, user)


async def check_link(message, user):
    vk_page_url = message.text
    if user.vk_user_url == vk_page_url:
        await bot.reply_to(message, f"Страница {vk_page_url} уже привязна к Вашему профилю",
                           disable_web_page_preview=True)
    else:
        if 'vk.com/' in vk_page_url:
            vk_id = await checker_instance.get_user_id(vk_page_url)
            try:
                user.vk_id = vk_id
                user.vk_user_url = vk_page_url
                await database_sync_to_async(user.save)()
                await bot.reply_to(message,
                                   text=message_text.vk_page_success,
                                   disable_web_page_preview=True)
                await get_status(message, user)
                await state_worker.reset_user_state(user)
            except Exception as e:
                if ValueError:
                    await bot.send_message(message.chat.id, message_text.vk_page_error)
                else:
                    await bot.send_message(message.chat.id, f"{e}")

        else:
            await bot.reply_to(message, text=message_text.vk_page_error)


async def get_status(message, user):
    user_id = user.tg_id
    status = user.get_status_display()
    url = user.vk_user_url
    await bot.send_message(message.chat.id,
                           f"Страница VK: {url}\nСтатус: {status}\nTelegram ID: {user_id}",
                           disable_web_page_preview=True)
    await state_worker.reset_user_state(user)


async def get_vip_code(message, user):
    vip_code_user_value = message.text
    try:
        vip_code_instance = await database_sync_to_async(VIPCode.objects.get)(vip_code=vip_code_user_value)
        user_vip_code = await database_sync_to_async(lambda: user.vip_code)()
        if user_vip_code:
            await bot.send_message(message.chat.id, "У Вас уже есть Вип код")
        else:
            user.vip_code = vip_code_instance
            user.status = UserTypes.VIP
            user.vip_end_date = timezone.now() + timedelta(days=30)
            vi_code_end_date = user.vip_end_date.strftime("%d.%m.%Y")
            await database_sync_to_async(user.save)()
            await bot.send_message(message.chat.id, f"✅Есть контакт! Срок действия кода - до {vi_code_end_date}\n"
                                                    f"Теперь ваши ссылки будут сразу попадать в очередь к другим участникам. Вам не нужно самостоятельно выполнять задания.")
        await state_worker.reset_user_state(user)
    except VIPCode.DoesNotExist:
        await bot.send_message(message.chat.id, "Неверный ВИП код")


@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'])
async def chat_member_handler(message):
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
                            if chat_user.status == UserTypes.VIP or chat_user.is_admin:
                                new_link_queue = await db_manager.create_link_queue(bot_user=chat_user, vk_link=vk_link)
                                await bot.send_message(user_id,
                                                       f"Ваша ссылка добавлена в очередь под "
                                                       f"№ {new_link_queue.queue_number}")
                            else:
                                await db_manager.create_link(bot_user=chat_user, vk_link=vk_link)
                                code_task = str(uuid.uuid4()).split('-')[0]
                                check_kb = keyboard_creator.create_check_keyboard()
                                tasks_qs = await database_sync_to_async(
                                    lambda: list(LinksQueue.objects.exclude(bot_user_id=chat_user.id).values()))()
                                done_qs = await database_sync_to_async(UserDoneLinks.objects.filter)(bot_user=chat_user)
                                done_ids = set(await database_sync_to_async(lambda: {q.link_id for q in done_qs})())
                                user_tasks = [task['vk_link'] for task in tasks_qs if task['id'] not in done_ids]

                                if user_tasks:
                                    await user_handler.mute_user(message)

                                    task_message_text = f"Ваше задание № {code_task}:\n" + '\n'.join(
                                        user_tasks)
                                    await db_manager.create_task_storage(bot_user=chat_user,
                                                                         message_text=task_message_text,
                                                                         code=code_task,
                                                                         chat_task=message_chat)
                                    await bot.send_message(user_id,
                                                           task_message_text,
                                                           disable_web_page_preview=True,
                                                           reply_markup=check_kb)
                                else:
                                    await bot.send_message(user_id, "Нет заданий")
                        else:
                            wrong_link = message.text
                            await bot.send_message(user_id, f"{message_text.link_error} {wrong_link}")
                    else:
                        wrong_message = message.text
                        await bot.send_message(user_id, f"{wrong_message} - не корректный формат ссылки!!!")
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
    user_id = await database_sync_to_async(BotUser.objects.get)(tg_id=callback.from_user.id)
    ts_qs = await database_sync_to_async(TaskStorage.objects.filter)(bot_user=user_id)
    last_chat_type = await database_sync_to_async(lambda: ts_qs.last())()
    chat_type = last_chat_type.chat_task
    if callback.data == 'check_button':
        data = await checker_instance.run(callback.message, user_id, chat_type)

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

