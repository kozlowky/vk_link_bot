from core.bot.models import LinksQueue, BotUser


class LinkDBManager:
    """"Класс - менеджер работы с моделью LinksQueue."""

    @staticmethod
    def create(obj: BotUser, **kwargs) -> LinksQueue:
        """Метод создания объекта ссылки пользователя."""
        link = LinksQueue.objects.create(
            bot_user=obj,
            **kwargs,
        )

        return link

    @staticmethod
    def update(link_id: int, **kwargs) -> None:
        link = LinksQueue.objects.filter(id=link_id).first()
        for attr, value in kwargs.items():
            setattr(link, attr, value)
        link.save()

