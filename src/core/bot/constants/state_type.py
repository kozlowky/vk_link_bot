from enum import IntEnum


class StateTypes(IntEnum):
    DEFAULT = 0
    VK_LINK = 1
    VIP_CODE = 2
    GET_STATUS = 3
    RESET_LINK = 4
    ACCEPT_TASK_MANUALLY = 5
    GET_TASK_LINKS = 6


USER_STATES_CHOICES = [
    (StateTypes.DEFAULT.value, "DEFAULT"),
    (StateTypes.VK_LINK.value, "VK_LINK"),
    (StateTypes.VIP_CODE.value, "VIP_CODE"),
    (StateTypes.GET_STATUS.value, "STATUS"),
    (StateTypes.RESET_LINK.value, "RESET_LINK"),
    (StateTypes.ACCEPT_TASK_MANUALLY.value, "ACCEPT_TASK_MANUALLY"),
    (StateTypes.GET_TASK_LINKS.value, "GET_TASK_LINKS")
]
