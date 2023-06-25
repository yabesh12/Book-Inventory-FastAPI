import enum
from enum import Enum


class ActionType(str, Enum):
    """
    Enum for BookActionType
    """
    BORROW = "BORROW"
    RETURN = "RETURN"



class RatingEnum(enum.Enum):
    """
    Book Rating Enum
    """
    ONE_STAR = 1
    TWO_STARS = 2
    THREE_STARS = 3
    FOUR_STARS = 4
    FIVE_STARS = 5