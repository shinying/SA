"""greedy dispatch v1
"""
import copy
from sys import stderr
from algo.model import TaskState, ShipState, ChargeTypeList
from .helper import find_possible_set, tug_to_charge_type, \
    get_pier_latlng, max_arrival_time, count_profit
from algo.predict_worktime import predict_worktime
from datetime import timedelta


def find_best_set(tug_set, task):
    max_profit = 0
    work_time = 0
    best_set = []
    for tugs in tug_set:
        wt = predict_worktime(task, tugs)
        arv_time = max_arrival_time(task, tugs)
        result = count_profit(task, tugs, wt, arv_time)
        if result['total_profit'] > max_profit:
            max_profit = result['total_profit']
            best_set = tugs
            work_time = wt

    return {"work_time": work_time, "best_set": best_set, "max_profit": max_profit}


def greedy_dispatch(tasks, tugs):
    """
    Args:
        tasks ([Task]): a list which stores the tasks to be planned

    Returns:
        tasks ([Task]): a list which stores the current processing and unprocessed tasks
    """
    # 利用噸位尋找收費型號
    tasks = copy.deepcopy(tasks)
    tugs = copy.deepcopy(tugs)
    tmp = []
    for task in tasks:
        if task.task_state == TaskState.UNPROCESSED_ASSIGNED or\
                task.task_state == TaskState.UNPROCESSED_UNASSIGNED:
            tmp.append(task)
    tasks = tmp
    tasks.sort(key=lambda x: x.start_time)
    #tugs = copy.deepcopy(tugs)
    stderr.write(
        "Dispatching {} tasks with Simple Greedy...\n".format(len(tasks)))

    for task in tasks:
        stderr.write("Dispathching task {} ...\n".format(task.id))

        # required_tug_list (type):[收費型號] ex: [117,118]
        required_tugs_list = task.req_types

        # possible set 是所有可用到的拖船組合
        # type: [Tug]
        # function: find_possible_set : 把已經預排的與正在工作的拖船剔除在拖船組合之外
        # 考慮_next_available_time
        possible_set = find_possible_set(tugs, required_tugs_list)
        alternative_set = []

        for s in possible_set:
            candidate = ChargeTypeList(tug_to_charge_type(s))
            required = ChargeTypeList(required_tugs_list)
            if candidate < required:
                alternative_set.append(s)

        possible_set = list(set(possible_set) - set(alternative_set))

        result = find_best_set(possible_set, task) if possible_set \
            else find_best_set(alternative_set, task)

        best_set = result['best_set']
        max_profit = result['max_profit']

        if not best_set:
            stderr.write("No best set!\n")
            continue

        # 更改每個tasks（複製的tasks）的
        # 1.task_state,
        # 2.work_time,
        # 3.tug(配對的tugs)
        # 4.調整tasks的開始時間
        task.task_state = TaskState.UNPROCESSED_ASSIGNED
        task.work_time = result['work_time']
        task.tugs = best_set
        arrival_time = max_arrival_time(task, task.tugs)
        task.delay_time = timedelta(minutes=max(0,arrival_time - task.start_time))
        task.start_time = task.start_time + task.delay_time

        for tug in task.tugs:
            tug.next_available_time = task.start_time + result['work_time']
            tug.pos = get_pier_latlng(task.to)

        for tug in tugs:
            tug.next_available_time = task.start_time + task.work_time
            tug.pos = get_pier_latlng(task.to)
    return [task.tugs for task in tasks], [task.start_time for task in tasks]
