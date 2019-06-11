"""parameters of the system
"""
from enum import Enum
from datetime import datetime, timedelta


SYSTEM_TIME = datetime(2017, 1, 1, 0, 0, 0, 0)
WINDOW_SIZE = timedelta(minutes=60)
TUG_STARTING_PLACE = 1001
URGENT_COST = 10
N_TUGS = 10
CALL_HELP_THR = timedelta(minutes=60)

TUG_SPEED = 8
SHIP_SPEED = 10


# dispatching-related

PENALTY = 100
WAITING_TIME = timedelta(minutes=40)

class ExecState(Enum):
    ERROR = -1
    SUCCESS = 0
    PROBLEM = 1
