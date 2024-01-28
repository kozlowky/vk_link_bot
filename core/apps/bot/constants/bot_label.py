from enum import IntEnum


class BotLabel(IntEnum):
    DEFAULT = 0
    ADVANCED = 1


BOT_LABEL_CHOICES = [
    (BotLabel.DEFAULT.value, "Лайки"),
    (BotLabel.ADVANCED.value, "Лайки/Подписка/Комменатрий"),

]