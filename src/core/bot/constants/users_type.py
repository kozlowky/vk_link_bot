from enum import IntEnum


class UserTypes(IntEnum):
    REGULAR = 0
    VIP = 1


USER_TYPES_CHOICES = [
    (UserTypes.REGULAR.value, "Обычный"),
    (UserTypes.VIP.value, "VIP"),

]