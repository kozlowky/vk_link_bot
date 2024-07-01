from typing import Optional

from core.bot.models import BotUser


class UserDBManager:
    """ Класс-менеджер работы с моделью BotUser. """

    @staticmethod
    def create(user_id: int, **kwargs) -> None:
        """ Метод создания или обновления данных пользователя бота. """

        user, _ = BotUser.objects.update_or_create(
            tg_id=str(user_id),
            defaults=kwargs,
        )

    @staticmethod
    def get(user_id: int) -> Optional[BotUser]:
        """ Метод получения пользователя бота. """

        user = BotUser.objects.filter(
            tg_id=str(user_id),
        ).first()
        return user

    @staticmethod
    def filter(**kwargs) -> BotUser:
        """ Метод проверки существования пользователя по заданным критериям """

        user = BotUser.objects.filter(
            **kwargs
        )
        return user
