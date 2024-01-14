from enum import IntEnum


class UserTypes(IntEnum):
    UNKNOWN = 0
    REGULAR = 1
    VIP = 2


USER_TYPES_CHOICES = [
    (UserTypes.UNKNOWN.value, "Неизвестно"),
    (UserTypes.REGULAR.value, "Обычный"),
    (UserTypes.VIP.value, "VIP"),

]