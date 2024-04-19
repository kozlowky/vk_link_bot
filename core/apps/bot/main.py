import logging
import re
import uuid
from datetime import timedelta

import telebot
from django.utils import timezone
from telebot import types
from telebot.async_telebot import AsyncTeleBot

import vk_api

from channels.db import database_sync_to_async

from django.conf import settings
from telebot.asyncio_helper import ApiTelegramException

from core.apps.bot.constants import message_text
from core.apps.bot.constants import chat_types
from core.apps.bot.constants.bot_label import BotLabel
from core.apps.bot.constants.state_type import StateTypes
from core.apps.bot.constants.users_type import UserTypes
from core.apps.bot.kb import KeyboardCreator, user_kb_list, start_menu_kb
from core.apps.bot.models import BotUser, LinkStorage, LinksQueue, UserDoneLinks, Chat, VIPCode, TaskStorage
from core.apps.bot.utils import state_worker, checker
from core.apps.bot.utils.db_handler import DatabaseManager
from core.apps.bot.utils.helpers import check_message, get_chat, check_recent_objects, check_current_task, accept_send_task
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

keyboard = keyboard_creator.create_user_keyboard()
check_kb = keyboard_creator.create_check_keyboard()


@bot.message_handler(commands=['start'], func=lambda message: message.chat.type == chat_types.PRIVATE_CHAT_TYPE)
async def send_welcome(message):
    user_id = message.from_user.id
    try:
        user = await database_sync_to_async(BotUser.objects.get)(tg_id=user_id)
        await state_worker.reset_user_state(user)
        await bot.reply_to(
            message,
            text=message_text.auth_user,
            reply_markup=keyboard
        )
    except BotUser.DoesNotExist:
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        username = message.from_user.username
        await db_manager.create_tg_user(
            tg_id=user_id,
            first_name=first_name,
            last_name=last_name,
            username=username)
        start_keyboard = keyboard_creator.create_start_keyboard()
        await bot.reply_to(
            message,
            text=message_text.start_message,
            reply_markup=start_keyboard
        )


@bot.message_handler(commands=['get_task'], func=lambda message: message.chat.type == chat_types.PRIVATE_CHAT_TYPE)
async def send_task(message):
    user = await database_sync_to_async(BotUser.objects.get)(tg_id=message.from_user.id)
    await state_worker.set_user_state(user, state=StateTypes.GET_TASK_LINKS)
    try:
        if user.is_admin:
            command, *args = message.text.split()
            if args:
                data = ' '.join(args)
                await get_last_task(message, data)
            else:
                await bot.reply_to(
                    message,
                    text='Не верный формат запроса'
                )
    except Exception as e:
        print(f"Error in send_task: {e}")


@bot.message_handler(commands=['accept_task'], func=lambda message: message.chat.type == chat_types.PRIVATE_CHAT_TYPE)
async def accept_task(message):
    user = await database_sync_to_async(BotUser.objects.get)(tg_id=message.from_user.id)
    await state_worker.set_user_state(user, state=StateTypes.ACCEPT_TASK_MANUALLY)
    try:
        if user.is_admin:
            command, *args = message.text.split()

            if args:
                data = ' '.join(args)
                await process_accept_manually(message, data)
            else:
                await bot.reply_to(
                    message,
                    text='Не верный формат запроса'
                )
    except Exception as e:
        print(f"Error in accept_task: {e}")


@bot.message_handler(commands=['remove_link'], func=lambda message: message.chat.type == chat_types.PRIVATE_CHAT_TYPE)
async def remove_link(message):
    user = await database_sync_to_async(BotUser.objects.get)(tg_id=message.from_user.id)
    await state_worker.set_user_state(user, state=StateTypes.RESET_LINK)
    try:
        if user.is_admin:
            command, *args = message.text.split()
            if args:
                data = ' '.join(args)
                await remove_link_queue(message, data)
            else:
                await bot.reply_to(
                    message,
                    text='Не верный формат запроса'
                )
    except Exception as e:
        print(f"Error in accept_task: {e}")


@bot.message_handler(
    func=lambda message: message.text in start_menu_kb and message.chat.type == chat_types.PRIVATE_CHAT_TYPE)
async def vip_choices(message):
    user = await database_sync_to_async(BotUser.objects.get)(tg_id=message.from_user.id)
    if message.text == "Есть, ввести":
        await bot.send_message(message.chat.id, text=message_text.vip_code_enter,
                               reply_markup=types.ReplyKeyboardRemove())
        await state_worker.set_user_state(user, state=StateTypes.VIP_CODE)
    else:
        await bot.reply_to(
            message,
            text=message_text.link_enter,
            reply_markup=keyboard
        )
        await state_worker.set_user_state(user, state=StateTypes.VK_LINK)


@bot.message_handler(
    func=lambda message: message.text in user_kb_list and message.chat.type == chat_types.PRIVATE_CHAT_TYPE)
async def handle_menu(message):
    user = await database_sync_to_async(BotUser.objects.get)(tg_id=message.from_user.id)
    if message.text == "Указать VK ID":
        await state_worker.set_user_state(user, state=StateTypes.VK_LINK)
        await bot.send_message(
            message.chat.id,
            text=message_text.link_enter
        )
    elif message.text == "Ввести ВИП код":
        await state_worker.set_user_state(user, state=StateTypes.VIP_CODE)
        await bot.send_message(
            message.chat.id,
            text=message_text.vip_code_enter
        )
    elif message.text == "Получить статус пользователя":
        await state_worker.set_user_state(user, state=StateTypes.GET_STATUS)
        await get_status(message, user)


@bot.message_handler(func=lambda message: True and message.chat.type == chat_types.PRIVATE_CHAT_TYPE,
                     content_types=['text'])
async def handle_text_message(message):
    user = await database_sync_to_async(BotUser.objects.get)(tg_id=message.from_user.id)
    current_state = await state_worker.get_user_state(user)

    if current_state == StateTypes.VK_LINK:
        await process_vk_link(message, user)
    elif current_state == StateTypes.VIP_CODE:
        await process_vip_code(message, user)


async def remove_link_queue(message, data):
    links_qs = await database_sync_to_async(LinksQueue.objects.filter)(vk_link=data)
    link = await database_sync_to_async(lambda: links_qs.last())()
    await bot.reply_to(message,
                       text=f"Ссылка {link.vk_link} удалена из очереди!",
                       disable_web_page_preview=True)
    await database_sync_to_async(link.delete)()


async def process_accept_manually(message, data):
    user = await database_sync_to_async(BotUser.objects.get)(vk_user_url=data)
    ts_qs = await database_sync_to_async(TaskStorage.objects.filter)(bot_user__vk_user_url=data, task_completed=False)

    if not await database_sync_to_async(ts_qs.exists)():
        await bot.send_message(
            chat_id=message.chat.id,
            text=f"У пользователя ID: {data.tg_id} нет заданий"
        )
    else:
        last_task = await database_sync_to_async(lambda: ts_qs.last())()
        accept_kb = keyboard_creator.create_accept_manualy()
        await bot.reply_to(message,
                           text=f"Пользователь {user.tg_id}\n\n{last_task.message_text}",
                           disable_web_page_preview=True,
                           reply_markup=accept_kb)


async def get_last_task(message, data):
    check_kb = keyboard_creator.create_check_keyboard()
    try:
        await database_sync_to_async(BotUser.objects.get)(vk_user_url=data)
        ts_qs = await database_sync_to_async(TaskStorage.objects.filter)(bot_user__vk_user_url=data,
                                                                         task_completed=False)
        if not await database_sync_to_async(ts_qs.exists)():
            await bot.send_message(chat_id=message.chat.id, text="Нет заданий")
        else:
            last_chat_type = await database_sync_to_async(lambda: ts_qs.last())()
            await bot.reply_to(message, text=f"{last_chat_type.message_text}", disable_web_page_preview=True,
                               reply_markup=check_kb)

    except BotUser.DoesNotExist:
        await bot.send_message(chat_id=message.chat.id, text=f"Пользователь: {data} не существует!")


async def process_vk_link(message, user):
    vk_page_url = message.text

    if user.vk_user_url == vk_page_url:
        await bot.reply_to(
            message=message,
            text=f"Страница {vk_page_url} уже привязана к Вашему профилю",
            disable_web_page_preview=True
        )
    else:
        if 'vk.com/' in vk_page_url:
            vk_id = await checker_instance.get_user_id(vk_page_url)
            try:
                user.vk_id = vk_id
                user.vk_user_url = vk_page_url
                await database_sync_to_async(user.save)()

                await bot.reply_to(
                    message=message,
                    text=message_text.vk_page_success,
                    disable_web_page_preview=True
                )
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


async def process_vip_code(message, user):
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
            vip_code_end_date = user.vip_end_date.strftime("%d.%m.%Y")
            await database_sync_to_async(user.save)()

            await bot.send_message(message.chat.id,
                                   f"✅Есть контакт! Срок действия кода - до {vip_code_end_date}\n"
                                   f"Теперь ваши ссылки будут сразу попадать в очередь к другим "
                                   f"участникам. Вам не нужно самостоятельно выполнять задания.",
                                   reply_markup=keyboard)

        await state_worker.reset_user_state(user)

    except VIPCode.DoesNotExist:
        await bot.send_message(
            message.chat.id,
            "Неверный ВИП код"
        )


async def create_link_for_previous(chat_user, link_data, count, chat_type, user_id) -> None:
    new_link_queue = await db_manager.create_link_queue(bot_user=chat_user,
                                                        vk_link=link_data.get("link"),
                                                        total_count=count,
                                                        chat_type=chat_type,
                                                        )

    if chat_user.status == UserTypes.VIP:
        await db_manager.create_link(bot_user=chat_user,
                                     vk_link=link_data.get("link"),
                                     comment=link_data.get("comment"),
                                     code="VIP",
                                     chat_type=chat_type
                                     )

    await bot.send_message(
        user_id,
        text=f"Ваша ссылка добавлена в очередь под № {new_link_queue.queue_number}"
    )


async def create_task_for_member(message, user_id, chat_user, link_data, count, chat_type):
    code = str(uuid.uuid4()).split('-')[0]
    await db_manager.create_link(bot_user=chat_user,
                                 vk_link=link_data.get("link"),
                                 comment=link_data.get("comment"),
                                 code=code,
                                 chat_type=chat_type
                                 )
    tasks_qs = await database_sync_to_async(
        lambda: list(
            LinksQueue.objects.exclude(bot_user_id=chat_user.id)
            .filter(send_count__lt=count, chat_type=chat_type)
            .values().distinct()
        )
    )()
    done_qs = await database_sync_to_async(UserDoneLinks.objects.filter)(
        bot_user=chat_user)
    done_ids = set(
        await database_sync_to_async(lambda: {q.link_id for q in done_qs})())
    user_tasks = [task['vk_link'] for task in tasks_qs if
                  task['id'] not in done_ids]
    if user_tasks:
        task_message_text = f"Ваше задание № {code}:\n" + '\n'.join(user_tasks)
        await db_manager.create_task_storage(bot_user=chat_user,
                                             message_text=task_message_text,
                                             code=code,
                                             chat_task=message.chat.username)
        await bot.send_message(user_id, task_message_text,
                               disable_web_page_preview=True,
                               reply_markup=check_kb)
        for task in tasks_qs:
            task_queue = await database_sync_to_async(LinksQueue.objects.get)(
                id=task.get("id"))
            task_queue.send_count += 1
            await database_sync_to_async(task_queue.save)()
    else:
        new_link_queue = await db_manager.create_link_queue(bot_user=chat_user,
                                                            vk_link=link_data.get("link"),
                                                            total_count=count,
                                                            chat_type=chat_type,
                                                            )
        await bot.send_message(user_id,
                               f"Сейчас нет заданий\n\nВаша ссылка добавлена в очередь под № {new_link_queue.queue_number}")


@bot.message_handler(func=lambda message: message.chat.type in ["group", "supergroup"])
async def chat_member_handler(message):
    user_id = message.from_user.id
    chat = await get_chat(message)
    chat_user = await database_sync_to_async(BotUser.objects.get)(tg_id=user_id)

    if not chat_user or not chat_user.vk_user_url:
        await bot.send_message(user_id, "Вы не привязали рабочую VK страницу")
        return

    count = await database_sync_to_async(lambda: chat.link_count)()
    chat_type = BotLabel(chat.chat_label).name
    link_data = await check_message(message)

    if link_data.get("error"):
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await bot.send_message(chat_id=message.from_user.id, text=link_data.get("error"))
        return

    if chat_user.is_admin:
        await create_link_for_previous(chat_user, link_data, count, chat_type, user_id)
    else:
        current_task = await check_current_task(chat_user, chat)
        if current_task:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            await bot.send_message(chat_id=message.from_user.id,
                                   text=f"Вы не завершили задание:\n\n{current_task.message_text}",
                                   disable_web_page_preview=True,
                                   reply_markup=check_kb)
        else:
            allow_links = await check_recent_objects(chat_user, chat, link_data)
            if allow_links != 0:
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
                await bot.send_message(chat_id=message.from_user.id,
                                       text=f"😢Не могу принять ссылку: {message.text}. От вашей предыдущей должно пройти {chat.reply_link_count} чужих ссылок. "
                                            f"Осталось: {allow_links}",
                                       disable_web_page_preview=True)

            elif chat_user.status == UserTypes.VIP:
                await create_link_for_previous(chat_user, link_data, count, chat_type, user_id)

            else:
                await create_task_for_member(message, user_id, chat_user, link_data, count, chat_type)


@bot.callback_query_handler(func=lambda callback: callback.data == 'check_button')
async def check_task(callback: types.CallbackQuery):
    user_id = await database_sync_to_async(BotUser.objects.get)(tg_id=callback.from_user.id)
    task_code = await checker_instance.get_task_code(callback.message.text)
    task_storage_qs = await database_sync_to_async(TaskStorage.objects.filter)(bot_user=user_id, code=task_code)
    last_task_storage = await database_sync_to_async(lambda: task_storage_qs.last())()
    chat_type = last_task_storage.chat_task

    chat_settings = await database_sync_to_async(Chat.objects.get)(
        bot_chats=f'https://t.me/{chat_type}')
    chat_label = BotLabel(chat_settings.chat_label).name

    if callback.data == 'check_button':

        links_in_task = re.findall(r'(https:\/\/vk\.com\/\S+)', callback.message.text)

        for link_in_task in links_in_task:
            link_queue_value = await database_sync_to_async(LinksQueue.objects.filter)(vk_link=link_in_task)

            if not link_queue_value:
                callback.message.text = callback.message.text.replace(link_in_task, '')



        if chat_label == "DEFAULT":
            data = await checker_instance.run_default_chat(callback.message, user_id)
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
                message = f"Задание № {task_code}\n\nВы не поставили лайк в следующих постах:\n\n" + "\n".join(
                    posts_without_like)
                check_kb = keyboard_creator.create_check_keyboard()

                try:
                    await database_sync_to_async(TaskStorage.objects.filter(code=task_code).update)(
                        message_text=message)
                    await bot.edit_message_text(chat_id=callback.message.chat.id,
                                                message_id=callback.message.message_id,
                                                text=message,
                                                disable_web_page_preview=True,
                                                reply_markup=check_kb)
                except ApiTelegramException:
                    message_ext = f"Вы не завершили предыдущее {message}"
                    await bot.edit_message_text(chat_id=callback.message.chat.id,
                                                message_id=callback.message.message_id,
                                                text=message_ext,
                                                disable_web_page_preview=True,
                                                reply_markup=check_kb)
                    await database_sync_to_async(TaskStorage.objects.filter(code=task_code).update)(
                        message_text=message)
            else:
                message = await accept_send_task(user_id)
                await bot.edit_message_text(chat_id=callback.message.chat.id,
                                            message_id=callback.message.message_id,
                                            text=message,
                                            disable_web_page_preview=True
                                            )

        if chat_label == "ADVANCED":
            data = await checker_instance.run_advanced_chat(callback.message, user_id)
            subs_data = []
            comments_data = []
            posts_without_like = []
            data_dict = {'subs': subs_data, 'comments': comments_data, 'likes': posts_without_like}

            for item in data:
                link = item.get('link')
                likes = item.get('likes')
                comments = item.get('comment')
                subs = item.get('sub')

                if not likes:
                    posts_without_like.append(link)

                if comments is None or comments < 5:
                    comments_data.append(link)

                if subs is None:
                    subs_data.append(link)

                tasks_qs = await database_sync_to_async(lambda: list(LinksQueue.objects.all().values()))()

                for task in tasks_qs:
                    link_present = any(link in sublist for sublist in data_dict.values())

                    if task['vk_link'] == link and not link_present:
                        task_instance = await database_sync_to_async(LinksQueue.objects.get)(id=task['id'])
                        await database_sync_to_async(UserDoneLinks.objects.get_or_create)(
                            bot_user=user_id,
                            link=task_instance
                        )

            if any(data_dict.values()):
                unique_link_without_likes = set(data_dict.pop('likes'))
                unique_out_comment = set(data_dict.pop('comments'))
                unique_out_subs = set(data_dict.pop('subs'))

                link_without_likes = list(unique_link_without_likes)
                out_comment = list(unique_out_comment)
                out_subs = list(unique_out_subs)

                global_message = (f"Задание № {task_code}\n")

                if link_without_likes:
                    link_message = "\n".join(link_without_likes)
                    global_message += f"Не поставлены лайки:\n{link_message}\n"

                if out_comment:
                    comment_message = "\n".join(out_comment)
                    global_message += f"Отсутствуют комментарии:\n{comment_message}\n"

                if out_subs:
                    subs_message = "\n".join(out_subs)
                    global_message += f"Отсутствует подписка:\n{subs_message}\n"

                check_kb = keyboard_creator.create_check_keyboard()
                try:
                    await database_sync_to_async(TaskStorage.objects.filter(code=task_code).update)(
                        message_text=global_message)
                    await bot.edit_message_text(chat_id=callback.message.chat.id,
                                                message_id=callback.message.message_id,
                                                text=global_message,
                                                disable_web_page_preview=True,
                                                reply_markup=check_kb)
                except ApiTelegramException:
                    message_ext = f"Вы не завершили предыдущее {global_message}"
                    await bot.edit_message_text(chat_id=callback.message.chat.id,
                                                message_id=callback.message.message_id,
                                                text=message_ext,
                                                disable_web_page_preview=True,
                                                reply_markup=check_kb)
                    await database_sync_to_async(TaskStorage.objects.filter(code=task_code).update)(
                        message_text=message_ext)
            else:
                message = await accept_send_task(user_id)
                await bot.edit_message_text(chat_id=callback.message.chat.id,
                                            message_id=callback.message.message_id,
                                            text=message,
                                            disable_web_page_preview=True
                                            )


@bot.callback_query_handler(func=lambda callback: callback.data == 'accept_manually')
async def manual_accept_task(callback: types.CallbackQuery):
    task_message = callback.message.text
    user_id = re.search(r'Пользователь (\S+)', task_message).group(1)
    task_code = re.search(r'№ (\S+)(?::)', task_message).group(1)
    sender_user = await database_sync_to_async(BotUser.objects.get)(tg_id=callback.from_user.id)
    target_user = await database_sync_to_async(BotUser.objects.get)(tg_id=user_id)

    task = await database_sync_to_async(TaskStorage.objects.get)(code=task_code)
    task.task_completed = True
    await database_sync_to_async(task.save)()

    link_storage = await database_sync_to_async(LinkStorage.objects.get)(code=task_code)
    link_storage.is_approved = True
    await database_sync_to_async(link_storage.save)()

    link = link_storage.vk_link
    link_queue = await db_manager.create_link_queue(bot_user=target_user, vk_link=link)
    await database_sync_to_async(link_queue.save)()

    done_link = await db_manager.create_done_list(bot_user=target_user, link=link_queue)
    await database_sync_to_async(done_link.save)()

    await bot.send_message(chat_id=callback.message.chat.id,
                           text=f"Задание № {task_code} переведено в статус ВЫПОЛНЕНО")
    await state_worker.reset_user_state(sender_user)



