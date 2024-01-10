from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

user_kb_list = ['Указать VK ID', 'Ввести ВИП код', 'Получить статус пользователя']
admin_kb_list = ['Аннулировать ссылку', 'Принять задание вручную', 'Прислать список ссылок по заданию']


class KeyboardCreator:
    def __init__(self, row_width=3, resize_keyboard=True):
        self.row_width = row_width
        self.resize_keyboard = resize_keyboard

    def create_keyboard(self, *buttons_text):
        keyboard = ReplyKeyboardMarkup(row_width=self.row_width, resize_keyboard=self.resize_keyboard)
        buttons = [KeyboardButton(text) for text in buttons_text]
        keyboard.add(*buttons)
        return keyboard

    def create_user_keyboard(self):
        user_buttons = user_kb_list
        return self.create_keyboard(*user_buttons)

    def create_admin_keyboard(self):
        all_buttons = user_kb_list + admin_kb_list
        return self.create_keyboard(*all_buttons)

    def create_check_keyboard(self):
        keyboard = InlineKeyboardMarkup()
        button = InlineKeyboardButton(text='Проверить', callback_data='check_button')
        keyboard.add(button)
        return keyboard

