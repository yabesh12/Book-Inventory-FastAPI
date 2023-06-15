from enum import Enum


class ActionType(str, Enum):
    """
    Enum for BookActionType
    """
    BORROW = "BORROW"
    RETURN = "RETURN"
