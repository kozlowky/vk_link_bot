from enum import IntEnum


class StateTypes(IntEnum):
    DEFAULT = 0
    VK_LINK = 1
    VIP_CODE = 2
    GET_STATUS = 3


USER_STATES_CHOICES = [
    (StateTypes.DEFAULT.value, "DEFAULT"),
    (StateTypes.VK_LINK.value, "VK_LINK"),
    (StateTypes.VIP_CODE.value, "VIP_CODE"),
    (StateTypes.GET_STATUS.value, "STATUS"),
]
