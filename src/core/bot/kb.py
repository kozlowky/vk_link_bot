from telebot.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from core.bot.constants import buttons


class KeyboardCreator:
    def __init__(self, row_width=3, resize_keyboard=True):
        self.row_width = row_width
        self.resize_keyboard = resize_keyboard

    def create_keyboard(self, *buttons_text):
        keyboard = ReplyKeyboardMarkup(
            row_width=self.row_width,
            resize_keyboard=self.resize_keyboard,
            one_time_keyboard=False
        )
        btns = [KeyboardButton(text) for text in buttons_text]
        keyboard.add(*btns)
        return keyboard

    def create_start_keyboard(self):
        vip_buttons = [buttons.ENTER_VIP_CODE, buttons.NO_VIP_CODE]
        return self.create_keyboard(*vip_buttons)

    def create_user_keyboard(self):
        user_buttons = [buttons.SET_VK_ID, buttons.ENTER_VIP_CODE, buttons.GET_USER_STATUS]
        return self.create_keyboard(*user_buttons)

    @staticmethod
    def create_check_keyboard():
        keyboard = InlineKeyboardMarkup()
        button = InlineKeyboardButton(
            text='Проверить',
            callback_data='check_button'
        )
        keyboard.add(button)
        return keyboard

    def create_accept_manualy(self):
        keyboard = InlineKeyboardMarkup()
        button = InlineKeyboardButton(
            text='Принять задание вручную',
            callback_data='accept_manually'
        )
        keyboard.add(button)
        return keyboard
