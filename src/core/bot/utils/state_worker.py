from core.bot.constants.state_type import StateTypes
from core.bot.models import BotUser


def get_user_state(user):
    """
    Получает состояние меню для пользователя.
    """
    return user.state_menu


def set_user_state(user, state):
    """
    Устанавливает состояние меню для пользователя.
    """
    user.state_menu = state
    user.save()
    return True


def reset_user_state(user):
    """
    Сбрасывает состояние меню пользователя на значение по умолчанию.
    """
    user.state_menu = StateTypes.DEFAULT.value
    user.save()
    return True


class UserStateHandler:
    """
    Класс для работы с состояниями
    """
    def __init__(self, user):
        self.user = user

    @property
    def state(self):
        """
        Получает состояние меню для пользователя.
        """
        return self.user.state_menu

    @state.setter
    def state(self, new_state):
        """
        Устанавливает состояние меню для пользователя.
        """
        self.user.state_menu = new_state
        self.user.save()

    def reset_state(self):
        """
        Сбрасывает состояние меню пользователя на значение по умолчанию.
        """
        self.user.state_menu = StateTypes.DEFAULT.value
        self.user.save()

