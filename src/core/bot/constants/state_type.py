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
    (StateTypes.GET_STATUS.value, "RESET_LINK"),
    (StateTypes.GET_STATUS.value, "ACCEPT_TASK_MANUALLY"),
    (StateTypes.GET_STATUS.value, "GET_TASK_LINKS")
]
