from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

user_kb_list = ['Указать VK ID', 'Ввести ВИП код', 'Получить статус пользователя']
start_menu_kb = ['Есть, ввести', 'Нет ВИП кода']


class KeyboardCreator:
    def __init__(self, row_width=3, resize_keyboard=True):
        self.row_width = row_width
        self.resize_keyboard = resize_keyboard

    def create_keyboard(self, *buttons_text):
        keyboard = ReplyKeyboardMarkup(row_width=self.row_width,
                                       resize_keyboard=self.resize_keyboard,
                                       one_time_keyboard=False)
        buttons = [KeyboardButton(text) for text in buttons_text]
        keyboard.add(*buttons)
        return keyboard

    def create_start_keyboard(self):
        vip_buttons = start_menu_kb
        return self.create_keyboard(*vip_buttons)

    def create_user_keyboard(self):
        user_buttons = user_kb_list
        return self.create_keyboard(*user_buttons)

    # def create_admin_keyboard(self):
    #     all_buttons = user_kb_list + admin_kb_list
    #     return self.create_keyboard(*all_buttons)

    def create_check_keyboard(self):
        keyboard = InlineKeyboardMarkup()
        button = InlineKeyboardButton(text='Проверить', callback_data='check_button')
        keyboard.add(button)
        return keyboard

    def create_accept_manualy(self):
        keyboard = InlineKeyboardMarkup()
        button = InlineKeyboardButton(text='Принять задание вручную', callback_data='accept_manually')
        keyboard.add(button)
        return keyboard

