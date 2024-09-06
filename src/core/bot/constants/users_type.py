from enum import IntEnum


class UserTypes(IntEnum):
    REGULAR = 0
    VIP = 1


USER_TYPES_CHOICES = [
    (UserTypes.REGULAR.value, "Обычный"),
    (UserTypes.VIP.value, "VIP"),

]


def status_display(user):
    status_mapping = {
        UserTypes.REGULAR: "Обычный",
        UserTypes.VIP: "VIP"
    }

    if user.is_admin:
        return "Администратор"

    return status_mapping.get(UserTypes(user.status), "Неизвестный статус")
