"""Define events which calls dispatching algorithm again
"""

from enum import Enum, IntEnum
from datetime import timedelta, datetime
from typing import List
from random import random, randint
from sys import stderr
from .model import Task, ChargeType, TaskState, TugState, ShipState, ChargeTypeList
from .utils.utility import count_move_dis, count_move_time, move_dis_to_time
from .utils.utility import get_oil_price, calculate_revenue
from .port import get_pier_latlng
from .simu_params import MAX_START_DELAY_TOLERANCE
from .settings import ExecState

class EventOrder(IntEnum):
    END = 0
    WORK_TIME_DELAY = 1
    CANCELED = 2
    START_TIME_DELAY = 3
    CHANGE_TYPES = 4
    COMFIRM = 5
    START = 6
    TEMP_NEED = 7
    DEFAULT = 8
    ROUTINE = 9


class Event:
    """Random events generated by simulator to trigger planning algorithm

    Types:
        ConfirmTask         The pilot accepts the preassigned tugs
        ChangeTypes:        The pilot changes the original required types
        Canceled:           The task is canceled before it starts
        StartTimeDelay:     The task is delayed before it starts
        WorkTimeDelay:      The task is delayed during operation
        TempNeed:           The pilot need more tugs during operation
        StartWork:          (Simulation only) The task starts
        EndWork:            (Simulation only) The task ends
    """

    def __init__(self, task: Task, time: datetime, order=EventOrder.DEFAULT):
        self.task = task
        self.time = time
        self.order = order

    def __str__(self):
        return "[{}] Task: {} Time: {} Tugs: {}".format(type(self).__name__, 
        self.task.id, self.time.strftime("%Y-%m-%d %H:%M"), [tug.tug_id for tug in self.task.tugs])

class Routine(Event):
    
    def __init__(self, task: Task, time: datetime):
        super().__init__(task, time, EventOrder.ROUTINE)

    def __str__(self):
        return "[Routine] Time: "+self.time.strftime("%Y-%m-%d %H:%M")
        
    def handle(self):
        pass
        
class ConfirmTask(Event):

    def __init__(self, task: Task, time: datetime):
        super().__init__(task, time, EventOrder.COMFIRM)

    def handle(self):

        # Check requirement
        assert len(self.task.tugs) == len(self.task.req_types),\
            "Requirement not satisfied. Require: {} Dispatch: {}".format(
            str([t.name for t in self.task.req_types]),
            str([tug.type.name for tug in self.task.tugs]))
        if self.task.id < 0:
            assert self.time >= self.task.start_time, \
                "Tugs for temp need tasks can only starts moving after the event happens"
        assert self.task.task_state is TaskState.UNPROCESSED_UNASSIGNED, \
            "Simulation error. Sorry...orz"

        self.task.task_state = TaskState.UNPROCESSED_ASSIGNED
        self.task.moving_cost = 0
        self.task.moving_time = timedelta(0)
        self.task.revenue = 0
        self.task.tugs_start_time.clear()

        move_times = []
        for tug in self.task.tugs:
            assert tug.state is TugState.FREE, "Wrong starting time: {} next_available_time {}".format(tug.tug_id, tug.next_available_time)
            tug.state = TugState.BUSY

            # count moving distance and time
            move_dis = count_move_dis(tug.pos, self.task.start)
            move_time = move_dis_to_time(move_dis)
            move_times.append(move_time)
            start_move = self.task.start_time_real - move_time
            self.task.tugs_start_time.append(start_move)

            # update tugs' state
            tug.ts.append(start_move)
            tug.ts.append(self.task.start_time_real)
            tug.next_available_time = self.task.start_time_real + self.task.work_time
            tug.pos = get_pier_latlng(self.task.to)
            tug.tasks.append(self.task)

            # calculate cost of the task
            self.task.moving_cost += move_dis * get_oil_price(tug.hp)
            self.task.moving_time += move_time
        
        assert len(self.task.tugs) == len(self.task.tugs_start_time), \
            "Simulation error. Sorry...orz"


class ChangeTypes(Event):

    def __init__(self, task: Task, time: datetime, req_types: List[ChargeType]):
        super().__init__(task, time)
        self.req_types = req_types

    def __str__(self):
        return "[{}] Task: {} Time: {} Change {} -> {}".format(
            type(self).__name__, self.task.id, self.time.strftime("%Y-%m-%d %H:%M"),
            [t.name for t in self.task.req_types], [t.name for t in self.req_types])

    def handle(self):
        self.task.req_types = self.req_types
        self.task.tug_cnt = len(self.req_types)

        # check if required type changes after all tugs started moving
        if self.task.task_state is TaskState.UNPROCESSED_ASSIGNED: 
            self.task.task_state = TaskState.UNPROCESSED_UNASSIGNED
            for tug in self.task.tugs:
                tug.ts.pop()
                tug.ts.pop()
                tug.tasks.pop()
                tug.state = TugState.FREE
                tug.next_available_time = self.time
                if tug.tasks:
                    tug.pos = get_pier_latlng(tug.tasks[-1].to)
            return ExecState.PROBLEM
                

class Canceled(Event):

    def __init__(self, task: Task, time: datetime):
        super().__init__(task, time, EventOrder.CANCELED)

    def handle(self):
        if self.task.task_state is TaskState.UNPROCESSED_ASSIGNED:
            for tug in self.task.tugs:
                tug.state = TugState.FREE
                tug.next_available_time = self.time
                tug.ts.pop()
                tug.ts.append(self.time)
                tug.ts.append(self.time)
                tug.pos = get_pier_latlng(tug.tasks[-1].start)
                if tug.tasks:
                    tug.tasks.pop()
        self.task.task_state = TaskState.CANCELED
        self.task.work_time = max(self.time - self.task.start_time_real, timedelta(0))


class StartTimeDelay(Event):

    def __init__(self, task: Task, time: datetime, delay: timedelta):
        super().__init__(task, time, EventOrder.START_TIME_DELAY)    
        self.delay = delay

    def __str__(self):
        return "[{}] Task: {} Time: {} Delay: {}".format(
            type(self).__name__, self.task.id, self.time.strftime("%Y-%m-%d %H:%M"),
            self.delay)

    def handle(self):
        self.task.start_time += self.delay
        self.task.start_time_real = max(self.task.start_time, self.task.start_time_real)

        if self.task.task_state is TaskState.UNPROCESSED_ASSIGNED:
            if self.delay.seconds > MAX_START_DELAY_TOLERANCE*60:
                for tug in self.task.tugs:
                    tug.ts.pop()
                    tug.ts.append(self.time)
                    tug.ts.append(self.time)
                    tug.next_available_time = self.time
                    tug.state = TugState.FREE
                    tug.pos = get_pier_latlng(tug.tasks[-1].start)
                    tug.tasks.pop()
                self.task.task_state = TaskState.UNPROCESSED_UNASSIGNED
                self.task.tugs = []
                return ExecState.PROBLEM
            else:
                for tug in self.task.tugs:
                    tug.ts.pop()
                    tug.ts.append(self.task.start_time_real)
                    tug.next_available_time = self.task.start_time_real + \
                        self.task.work_time


class WorkTimeDelay(Event):

    def __init__(self, task: Task, time: datetime, delay: timedelta):
        super().__init__(task, time, EventOrder.WORK_TIME_DELAY)
        self.delay = delay

    def __str__(self):
        return "[{}] Task: {} Time: {} Delay: {}".format(
            type(self).__name__, self.task.id, self.time.strftime("%Y-%m-%d %H:%M"),
            self.delay)

    def handle(self):
        self.task.work_time += self.delay
        for tug in self.task.tugs:
            tug.next_available_time += self.delay


class TempNeed(Event):

    def __init__(self, task: Task, time: datetime, req_types: List[ChargeType]):
        super().__init__(task, time)
        self.req_types = req_types

    def __str__(self):
        return "[{}] Task: {} Time: {} Tugs: {}".format(type(self).__name__, 
            self.task.id, self.time.strftime("%Y-%m-%d %H:%M"), 
            [ttype.name for ttype in self.req_types])

    def handle(self):
        if self.task.task_state is TaskState.PROCESSED:
            return
        self.task.tmp_need_time = self.time
        self.task.req_types.extend(self.req_types)


class StartWork(Event):

    def __init__(self, task: Task, time: datetime):
        super().__init__(task, time, EventOrder.START)

    def handle(self):
        assert self.task.task_state is not TaskState.PROCESSING_ASSIGNED, \
            "Repetitive start"
        self.task.task_state = TaskState.PROCESSING_ASSIGNED
        

class EndWork(Event):

    def __init__(self, task: Task, time: datetime):
        super().__init__(task, time, EventOrder.END)

    def handle(self):
        self.task.task_state = TaskState.PROCESSED
        for tug in self.task.tugs:
            assert tug.next_available_time == self.time, \
                "Wrong working time: {}. Next available: {}. Task working time: {}".format(
                    tug.tug_id, tug.next_available_time.strftime("%Y-%m-%d %H:%M"), 
                    self.task.work_time
                )
            tug.state = TugState.FREE
            tug.ts.append(self.time)
            