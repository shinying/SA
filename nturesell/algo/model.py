""" Defining models eg. Ship, Tug, Task ... etc
"""
from enum import Enum, IntEnum
from collections import deque
from datetime import time, datetime, timedelta
from sys import stderr
from .settings import SHIP_SPEED, TUG_SPEED, URGENT_COST, ExecState
from .predict_worktime import predict_worktime

## -------------- Tug-Related Classes --------------

class TugState(Enum):
    """States of tugs which are considered when planning

    Attributes:
        FREE:        a tug which is ready to work immediately
        BUSY:        a tug which is busy working on a specific tesk
        UNAVAILABLE: a tug which is either broken or out of order
    """
    FREE = 0
    BUSY = 1
    UNAVAILABLE = 2

class Tug():
    """Main entities to be planned

    Attributes:
        tug_id (int):         ID of the tug
        pos ((float, float)): Current position of the tug, a pair of latitude and lontitude
        type (ChargeType):    Charging type
        hp (int):             Horsepower of the tug
        velo (int):           Velocity, default 8kt
        state (TugState):     Current state of the tug, FREE, BUSY or UNAVAILABLE
        tasks (Task):         Tasks served by the tug
        next_available_time:  The time a busy tug finish its current task
        company(Company):     The tug belongs to KHPORT or GANGCHIN

        tasks ([Task]):       A list of tasks the tug have served
        ts ([datetime]):      A list of timestamp when the tug starts to move, starts and ends a task

    """

    def __init__(self, tug_id, cur_pos, charge_type, hp, 
        next_available_time, duty_period, state=TugState.FREE, velo=TUG_SPEED):
        self.tug_id = tug_id
        self.pos = cur_pos
        self.type = charge_type
        self.hp = hp
        self.state = state
        self.velo = velo
        self.next_available_time = next_available_time
        self.company = get_tug_company(tug_id)

        self.duty_period = duty_period
        self.tasks = deque([])
        self.ts = deque([])

    def __str__(self):
        return (
            "------------ Tug {} ------------\n".format(self.tug_id) +
            "- type: {} hp: {} state: {}  company: {} \n".format(self.type.name, self.hp, self.state, self.company) +
            "- pos: {}\n- next available time: {}".format(self.pos, self.next_available_time))

    def __eq__(self, other):
        return self.tug_id == other.tug_id

    def __hash__(self):
        return hash(self.tug_id)


class ChargeType(IntEnum):
    """Types of tugs which are used in charging and planning.
    Values of attributes correpond to weights according to the dispatching rule
    """

    TYPE_117 = 117
    TYPE_118 = 118
    TYPE_119 = 119
    TYPE_120 = 120
    TYPE_0   = 121 # 130


class ChargeTypeList(object):
    """Helper class for type comparisons
    """

    def __init__(self, charge_type_list):
        self.types = sorted(charge_type_list)

    def __eq__(self, other):
        if len(self.types) != len(other.types):
            return False
        else:
            for type1, type2 in zip(self.types, other.types):
                if type1 != type2:
                    return False
        return True

    def __ge__(self, other):
        if len(self.types) != len(other.types):
            return False
        else:
            for type1, type2 in zip(self.types, other.types):
                if type1 < type2:
                    return False
        return True


## -------------- Task-Related Classes --------------

class TaskState(IntEnum):
    """States of task describing
        if tugs are assigned (UNASSIGNED or ASSIGNED)
        if the task is finished (UNPROCESSED, PROCESSING, or PROCESSED)
    """

    UNPROCESSED_UNASSIGNED = 0
    UNPROCESSED_ASSIGNED = 1
    PROCESSING_ASSIGNED = 2
    PROCESSED = 3
    CANCELED = 4


class TaskPriority(IntEnum):
    """A task with ship_state ShipState.IN and TmpTask are URGENT,
    others are default
    """

    DEFAULT = 1
    URGENT = URGENT_COST


class Side(Enum):
    LEFT = 'L'
    RIGHT = 'R'
    OPTIONAL = 'O'


class Task():
    """
    Attributes:
        id (int):                   ID
        ship (Ship):                Ship
        tug_cnt (int):              The required number of tugs
        req_types ([ChargeType]):   The required types of tugs
        ship_state (ShipState):     IN, OUT, or TRANSFER
        start_time (datetime):      The time when the task should starts
        start_time_real (datetime): The time when the task actually starts
        last_tug_move (datetime):   The time when the last tug starts moving
        start (int):                Origin, port number
        to (int):                   Destination, port number
        side (Side):                The left or right side with which the ship parks
        priority (TaskPriority):    The priority of task

        task_state (TaskState):     Whether a task is PROCESSED or ASSIGNED
        events ([Event]):           Simulation events involving the task
        tugs ([Tug]):               tugs handling the task
        work_time (datetime):       Working time predicted by a model
        extra_wait (timedelta):     Extra waiting time due to temp need
        tmp_need_time (datetime):   The time when temp need happens (optional)
        wind_lev(int):              the wind level of the task when start
        company(Company):           the task belong to KHPORT or GANGCHIN

    """
    
    def __init__(self, i, ship, tug_cnt, ship_state, start_time, start, dest, company, \
        side=Side.OPTIONAL, priority=TaskPriority.DEFAULT, wind_lev = 3):
        self.id = i
        self.ship = ship
        self.tug_cnt = tug_cnt
        self.req_types = find_req_tug_types(ship.weight, tug_cnt)
        self.ship_state = ship_state
        self.start_time = self.start_time_real = self.last_tug_move = start_time
        self.start = start
        self.to = dest
        self.side = side
        self.priority = priority
        self.wind_lev = self.wind_to_wind_lev(wind_lev)
        self.company = company

        # Don't need arguments
        self.task_state = TaskState.UNPROCESSED_UNASSIGNED
        self.events = []
        self.tugs = []
        self.work_time = timedelta(0)
        self.extra_wait = timedelta(0)
        self.tmp_need_time = None

        # For simulation result
        self.moving_cost = 0
        self.moving_time = timedelta(0)
        self.waiting_cost = 0
        self.waiting_time = timedelta(0)
        self.tugs_start_time = []
        self.revenue = 0
        self.profit = 0

    def __str__(self):
        return (
            "------------ Task {} ------------\n".format(self.id) +
            "- ship {}\n".format(self.ship.ship_id) +
            "- Depart at: {}\n".format(self.start_time.strftime("%Y-%m-%d %H:%M")) +
            "- From {} to {}\n".format(self.start, self.to) +
            "- Goes: {}\n- Side: {}\n".format(self.ship_state.name, self.side.name))

    def __eq__(self, other):
        return self.id == other.id

    def update_work_time(self):
        self.work_time = predict_worktime(self, self.tugs)

    def assign_tugs(self, tugs, start_time):
        self.tugs = tugs
        if tugs:
            self.update_work_time()

        if start_time is None:
            start_time = self.start_time
        self.start_time_real = start_time
        
    def wind_to_wind_lev(self,wind):
        if wind <= 1.5:
            return 1
        elif wind > 1.5 and wind <= 3.3:
            return 2
        elif wind > 3.3 and wind <= 5.4:
            return 3
        elif wind > 5.4 and wind <= 7.9:
            return 4
        elif wind > 7.9 and wind <= 10.7:
            return 5
        elif wind > 10.7 and wind <= 13.8:
            return 6
        else:
            return 7 

class TmpTask(Task):
    """Temporary task for temp need
    """

    def __init__(self, task, req_types, time):
        super().__init__(-1 * task.id, task.ship, len(req_types), task.ship_state, \
            time, task.start, task.to, task.side, TaskPriority.URGENT)

        self.ori_task = task
        self.req_types = req_types

    def update_work_time(self):
        self.work_time = self.start_time_real + self.ori_task.work_time - self.start_time


## -------------- Ship-Related Classes --------------

class Ship():
    """Characteristics of ships would be considered in planning

    Attributes:
        id (int):        ID of the ship
        pos ((int,int)): Current position of the ship, a pair of latitude and longitude
        weight (int):    Ship weight
        velo (int):      Velocity, default 10kt
    """

    def __init__(self, ship_id, cur_pos, weight, velo=SHIP_SPEED):
        self.ship_id = ship_id
        self.pos = cur_pos
        self.weight = weight
        self.velo = velo

    def __str__(self):
        return("Ship {}: weight = {}".format(self.ship_id, self.weight))


class ShipState(Enum):
    IN = 'I'
    OUT = 'O'
    TRANSFER = 'T'

class Company(Enum):
    KHPORT = 'K'
    GANGCHIN = 'G'


# # # Helper Function # # #

def find_req_tug_types(weight, tug_cnt):
    """
    Args:
        weight (Task.ship.weight) : ship weight
        tug_cnt (int):              the required number of tugs

    Returns:
        required_tug_list([ChargeType]): a list of required tug type
    """
    tug_cnt -= 1
    if weight < 5000:
        return ([[ChargeType.TYPE_117], [ChargeType.TYPE_117, ChargeType.TYPE_117]][tug_cnt])
    elif weight < 10000:
        return ([[ChargeType.TYPE_118], [ChargeType.TYPE_117, ChargeType.TYPE_117]][tug_cnt])
    elif weight < 15000:
        return ([[ChargeType.TYPE_118], [ChargeType.TYPE_117, ChargeType.TYPE_118]][tug_cnt])
    elif weight < 30000:
        return ([[ChargeType.TYPE_119], [ChargeType.TYPE_118, ChargeType.TYPE_119]][tug_cnt])
    elif weight < 45000:
        return ([[ChargeType.TYPE_119], [ChargeType.TYPE_119, ChargeType.TYPE_119]][tug_cnt])
    elif weight < 60000:
        return ([[ChargeType.TYPE_120], [ChargeType.TYPE_120, ChargeType.TYPE_120]][tug_cnt])
    elif weight < 100000:
        return ([[ChargeType.TYPE_0], [ChargeType.TYPE_0, ChargeType.TYPE_0]][tug_cnt])
    else:
        return ([ChargeType.TYPE_0, ChargeType.TYPE_0])

def get_tug_company(tug_id):
    tugs_khport = [104,106,108,109,151,152,153,155,161,162,163,165,171,172,181,182]
    tugs_gangchin = [112,145,241,321,322,451,101,143,245,303,306,401,301,302,308]
    if tug_id in tugs_khport:
        return(Company.KHPORT)
    elif tug_id in tugs_gangchin:
        return(Company.GANGCHIN)

