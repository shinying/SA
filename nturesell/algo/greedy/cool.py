"""Cool dispatch, a dispatching algorithm example
"""

from sys import stderr
from datetime import timedelta, datetime
from typing import List
from collections import deque
from ..model import TaskState, Task, Tug, ChargeType
from ..settings import PENALTY, WAITING_TIME
from ..utils.utility import count_move_time, get_oil_price, count_move_dis, get_pier_latlng
from ..predict_worktime import predict_worktime


class CoolTug():

    def __init__(self, tug: Tug):
        self.tug = tug
        self.next_available_time = tug.next_available_time
        self.pos = tug.pos

    @property
    def tug_id(self):
        return self.tug.tug_id

    @property
    def type(self):
        return self.tug.type

    @property
    def hp(self):
        return self.tug.hp


def cool_dispatch(tasks, tugs, helped_tugs, call_help, call_help_thr, \
    sys_time, verbose=True):
    """
    Args:
        tasks: tasks to be dispatched
        tugs: tugs currently available
        sys_time: current time in simulator

    Returns:
        [[Tug]]: a list of lists of tugs in the same order as the given tasks
        [datetime]: a list of times at which the tasks actually start
    """

    tugs = [CoolTug(tug) for tug in sorted(tugs, key=lambda t: t.type)]
    
    res = []
    times = []

    for task in tasks:
        if verbose:
            print("Dispathching task {} ...".format(task.id))

        # Find require charge type and remove unqualified tugs from available tug set
        required_tugs_list = task.req_types

        # check if it's tmp need task
        tugs_que = deque(filter(lambda t: t.tug not in task.ori_task.tugs and \
            t.type >= required_tugs_list[0], tugs)) if task.id < 0 else \
                deque(filter(lambda t: t.type >= required_tugs_list[0], tugs))

        my_waiting_time = WAITING_TIME
        best_set = []
        for req in required_tugs_list:
            candid_tugs = deque([])
            min_cost = 0
            elected_tug = None
            give_up = False
            req_type = req

            while not give_up:

                # First look up type-matched tugs
                while tugs_que and tugs_que[0].type < req_type:
                    tugs_que.popleft()

                while tugs_que and tugs_que[0].type == req_type:
                    tug = tugs_que.popleft()
                    candid_tugs.append(tug)
                    time_cost = (tug.next_available_time + count_move_time(tug.pos, task.start)
                                 - task.start_time_real)

                    if time_cost <= my_waiting_time:
                        cost = time_cost.seconds / 60 * PENALTY + get_oil_price(tug.hp) * \
                            count_move_dis(tug.pos, task.start)
                        if min_cost == 0:
                            min_cost = cost
                            elected_tug = tug
                        elif cost < min_cost:
                            min_cost = cost
                            elected_tug = tug
                
                if elected_tug:
                    best_set.append(elected_tug)
                    
                    # Put other tugs back to tugs queue
                    put_back = filter(lambda t: t is not elected_tug, candid_tugs)
                    tugs_que.extendleft(put_back)
                    break

                # No type-matched tugs available within the maximum waiting time
                elif req_type < ChargeType.TYPE_0:
                    req_type = ChargeType(req_type+1)

                elif my_waiting_time <= timedelta(hours=5):
                    my_waiting_time += timedelta(minutes=20)
                    tugs_que.extendleft(candid_tugs)
                    req_type = req

                else:
                    for i in range(len(tugs)-1, -1, -1):
                        if tugs[i] not in best_set:
                            if task.id < 0 and tugs[i] in task.ori_task.tugs:
                                continue
                            best_set.append(tugs[i])
                            break
                    give_up = True
         
        if len(best_set) != len(required_tugs_list):
            if verbose:
                print("Task", task.id, "No good choices!")
            res.append([])
            times.append(task.start_time)
            continue
        
        choices = [best.tug for best in best_set]
        choices.sort(key=lambda tug: tug.type)
        res.append(choices)  
        
        work_time = predict_worktime(task, choices)
        
        max_move_time = timedelta(0)
        move_times = [count_move_time(tug.pos, task.start) for tug in best_set]
        next_time = [tug.next_available_time+mt for tug, mt in zip(best_set, move_times)]
        start_time_real = max(task.start_time, max(next_time))
        max_move_time = max(move_times)

        if task.id < 0: # temp need task
            start_time_real = max(start_time_real-max_move_time, task.start_time) \
                + max_move_time
            work_time = task.ori_task.start_time_real + task.ori_task.work_time \
                - task.start_time
            for t in tugs:
                if t.tug in task.ori_task.tugs:
                    t.next_available_time += max(start_time_real - task.start_time, timedelta(0))

        times.append(start_time_real)
        
        for tug in best_set:
            tug.next_available_time = start_time_real + work_time
            tug.pos = get_pier_latlng(task.to)
        if verbose:
            print("> Tugs:", [tug.tug_id for tug in choices], start_time_real.strftime("%H:%M"))

    return res, times

