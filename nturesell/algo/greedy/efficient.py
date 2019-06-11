"""greedy dispatch 
"""

import copy
from sys import stderr
from datetime import timedelta

from .helper import tug_to_charge_type
from .helper import max_arrival_time, count_profit
from ..model import TaskState, TugState, ShipState, ChargeTypeList, Tug
from ..settings import PENALTY, WAITING_TIME, SYSTEM_TIME
from ..port import get_pier_latlng
from ..predict_worktime import predict_worktime
from ..utils.utility import count_move_time


class ETug():

    def __init__(self, tug):
        self.tug = tug
        self.next_available_time = tug.next_available_time
        self.pos = tug.pos

    @property
    def type(self):
        return self.tug.type

    @property
    def hp(self):
        return self.tug.hp

    @property
    def tug_id(self):
        return self.tug.tug_id


def efficient_dispatch(tasks, tugs, time):
    """
    Args:
        tasks ([Task]): a list which stores the tasks to be planned
        tugs ([Tug]): a list of tugs avaiable 
        time (datetime): current time in simulator

    Returns:
        [[Tug]]: a list of lists of tugs in the same order as the given tasks
        [datetime]: a list of times at which the tasks actually start
    """

    # print("Dispatching {} tasks with Efficient Greedy...\n".format(len(tasks)), file=stderr)

    tasks = copy.deepcopy(tasks)
    tugs = [ETug(tug) for tug in tugs]

    for task in tasks:
        # print("Dispathching task {} ...\n".format(task.id), file=stderr)

        # 先用required_tug_set算出這個task的work_time
        required_tugs_list = task.req_types
        tug_set = []
        tug_set = sorted(tugs, key=lambda x: x.type)
        best_set = []

        for i in required_tugs_list:
            l = 0
            while l < len(tug_set):
            # for l in range(len(tug_set)):
                temp_move_time = count_move_time(tug_set[l].pos, task.start)
                if tug_to_charge_type(tug_set)[l] >= i and \
                ((tug_set[l].next_available_time + temp_move_time - task.start_time <= WAITING_TIME ) or \
                (tug_set[l].next_available_time + temp_move_time - SYSTEM_TIME <= WAITING_TIME )):
                    if task.id < 0:
                        found = True
                        for t in task.ori_task.tugs:
                            if tug_set[l].tug_id == t.tug_id:
                                found =False
                                break
                        if found:
                            best_set.append(tug_set[l])
                            del tug_set[l]
                            break
                    else :
                        best_set.append(tug_set[l])
                        del tug_set[l]
                        break
                l += 1
       
        if len(best_set) != len(required_tugs_list) and task.id > 0:
            # stderr.write("No best set!\n")
            best_set = []
            task.start_time += timedelta(minutes = 10)
            task.delay_time += timedelta(minutes = 10)
            continue

        # 更改每個tasks（複製的tasks）的
        # 1.task_state,
        # 2.work_time,
        # 3.tug(配對的tugs)
        # 4.調整tasks的開始時間

        task.tugs = [best.tug for best in best_set]
        work_time = predict_worktime(task, best_set)

        arrival_time = max_arrival_time(task, best_set)
        max_move_time = max([count_move_time(tug.pos, task.start) for tug in best_set])
        task.delay_time = max(timedelta(0), arrival_time-task.start_time)
        task.start_time = task.start_time + task.delay_time

        if task.id < 0: # temp need task
            task.start_time = max(task.start_time-max_move_time, task.start_time-task.delay_time) \
                + max_move_time
            work_time = task.ori_task.start_time + task.ori_task.work_time \
                - (task.start_time-task.delay_time)

        for tug in best_set:
            tug.next_available_time = task.start_time + work_time
            tug.pos = get_pier_latlng(task.to)
        for tug in best_set:
            for i in range(len(tugs)):
                if tugs[i].tug_id == tug.tug_id:
                    tugs[i].next_available_time = task.start_time + work_time
                    tugs[i].pos = get_pier_latlng(task.to)
            
    return [task.tugs for task in tasks], [task.start_time for task in tasks]


