from sys import stderr
from datetime import timedelta
from ..greedy.helper import tug_to_charge_type
from ..greedy.helper import max_arrival_time, count_profit
from ..model import TaskState, TugState, ShipState, ChargeTypeList, Tug, Task
from ..settings import PENALTY, WAITING_TIME, SYSTEM_TIME
from ..port import get_pier_latlng
from ..predict_worktime import predict_worktime
from ..utils.utility import count_move_time
import copy
from itertools import combinations

class GTug():

    def __init__(self, tug: Tug):
        self.tug = tug
        self.id = tug.tug_id
        self.next_available_time = tug.next_available_time
        self.pos = tug.pos
        self.jobs = []
        self.state = tug.state
        self.ts = tug.ts
        self.tasks = tug.tasks 
        self.company = tug.company
        

    @property
    def type(self):
        return self.tug.type

    @property
    def hp(self):
        return self.tug.hp

    @property
    def tug_id(self):
        return self.tug.tug_id


def candSet(tsk, tgs, match):
    # 產生所有的候選組合
    requires = tsk.req_types
    cands = []
    if match == 'over':
        for i in range(len(requires)):
            for tg in tgs:
                if tg in cands:
                    continue
                if tg.type >= requires[i]:
                    cands.append(tg)
    elif match == 'every':
        for tg in tgs:
            cands.append(tg)

    cands_comb = combinations(cands, len(requires))   

    return cands_comb

def elongate(tsk, tg_set):
    # for each tug in tg_set, for each of its job, elongate its starting and ending times 
    # according to its location and the new job tsk's location
    original_lst = []
    
    if len(tg_set) == 1:
        for i in range(len(tg_set[0].jobs)):
            s = tg_set[0].jobs[i][0] - count_move_time(get_pier_latlng(tsk.to), tg_set[0].jobs[i][2])
            e = tg_set[0].jobs[i][1] + count_move_time(get_pier_latlng(tg_set[0].jobs[i][3]), tsk.start)
            original_lst.append([s,e])
    else:    
        for i in tg_set:
            original_lst.append([]) 
        for i in range(len(tg_set)):
            for j in range(len(tg_set[i].jobs)):
                original_lst[i].append(tg_set[i].jobs[j][0] - count_move_time(get_pier_latlng(tsk.to), tg_set[i].jobs[j][2]))
                original_lst[i].append(tg_set[i].jobs[j][1] + count_move_time(get_pier_latlng(tg_set[i].jobs[j][3]), tsk.start))

    return original_lst

def mergeTimeline(tsk, tg_set):
    elong_lst = elongate(tsk, tg_set)
    final_lst = []
    for tg_times in elong_lst:
        for i in range(len(tg_times) // 2):
            final_lst.append([tg_times[2 * i], tg_times[2 * i + 1]])

    final_lst.sort(key=lambda x: x[0])
    if len(final_lst)==0:
        merged = []
    else:
        merged = [final_lst[0]]
    for current in final_lst:
        previous = merged[-1]
        if current[0] <= previous[1]:
            previous[1] = max(previous[1], current[1])
        else:
            merged.append(current)

    return merged


def cal_delay(tsk, tg_set):
    work_time = predict_worktime(tsk, tg_set)
    next_available_time = max([tg.next_available_time for tg in tg_set])
    if len(tg_set)==1: # for one tug set, only elongate timeline
        merged = elongate(tsk, tg_set)
    else: # for two or three tug set, merge elongated timeline
        merged = mergeTimeline(tsk, tg_set) 

    # merged 存的是合併後的已加上移動時間的工作時間軸e.g.[[2, 6], [12, 18], [25, 30]]兩兩一組
    s_time = tsk.start_time
    e_time = tsk.start_time+work_time
    mt_TugtoTask = max([count_move_time(tg.pos, tsk.start) for tg in tg_set])

    delaytime = timedelta(0)
    if len(merged) == 0:
        delaytime = next_available_time + mt_TugtoTask - s_time
        if delaytime < timedelta(0):
            delaytime = timedelta(0)
        return delaytime

    else:
        for i in range(len(merged)):
            if i == 0:
                prev = next_available_time + mt_TugtoTask
            else:
                prev = merged[i-1][1]

            if s_time > prev:

                if e_time < merged[i][0]: # can insert
                    delaytime = timedelta(0)
                    return delaytime
                else:
                    for j in range(i+1, len(merged)):
                        if work_time <= (merged[j][0] - merged[j-1][1]): # can delay insert
                            delaytime = merged[j-1][1] - s_time
                            return delaytime

                    delaytime = merged[len(merged)-1][1] - s_time
            else:
                #需處理如果開始時間在拖船可用時間之前
                delaytime = timedelta(minutes=999999)

    return delaytime


def insertjob(nt, tg, jobs):
    # update jobs list of tug
    mt_f = timedelta(0)
    mt_b = timedelta(0)
    
    if len(jobs)==0:
        jobs.insert(0, nt)
        return jobs, True
    else:
        for i in range(len(jobs)):
            if i==0:
                prev = tg.next_available_time
                mt_f = count_move_time(tg.pos, nt[2])
                mt_b = count_move_time(get_pier_latlng(nt[3]), jobs[i][2])
                nt[0] = nt[0] - mt_f
                nt[1] = nt[1] + mt_b
            else:
                prev = jobs[i-1][1]
                mt_f = count_move_time(get_pier_latlng(jobs[i-1][3]), nt[2]) 
                mt_b = count_move_time(get_pier_latlng(nt[3]), jobs[i][2])
                nt[0] = nt[0] - mt_f
                nt[1] = nt[1] + mt_b
            
            if nt[1] <= jobs[i][0] and nt[0] >= prev: 
                nt[0] = nt[0] + mt_f
                nt[1] = nt[1] - mt_b
                jobs.insert(i, nt)
                return jobs, True

            else:
                nt[0] = nt[0] + mt_f
                nt[1] = nt[1] - mt_b
                
        mt_f = count_move_time(get_pier_latlng(jobs[len(jobs)-1][3]), nt[2])

        if nt[0]-mt_f >= jobs[len(jobs)-1][1]:
            jobs.append(nt)
            return jobs, True


    return jobs, False


def timeline_dispatch(tsks, tgs, help_tug, help, systime):
    """
    Args:
        tasks ([Task]): a list which stores the tasks to be planned
        tugs ([Tug]): a list of tugs avaiable 

    Returns:
        [[Tug]]: a list of lists of tugs in the same order as the given tasks
        [datetime]: a list of times at which the tasks actually start
    """
    threshold = timedelta(minutes=30)
    tasks = copy.deepcopy(tsks)
    tugs = [GTug(tg) for tg in tgs]
    tugs.sort(key = lambda x: x.type)
    
    tasks_order = copy.deepcopy(tsks)
    tasks_order.sort(key = lambda x: x.start_time)

    stderr.write("Dispatching {} tasks with Gogo ...\n".format(len(tasks)))
    
    '''-----task 分類-----'''
    tasks_priority = []
    tasks_ones = []
    tasks_tempNeed = []
    for task in tasks_order:
        if task.id < 0: # temp need
            tasks_tempNeed.append(task)
        elif len(task.req_types) >= 2:
            tasks_priority.append(task)
        else:
            tasks_ones.append(task)

    '''--------處理 Temp Need---------'''
    for task in tasks_tempNeed:
        stderr.write("Dispatching task {} \n".format(task.id))
        best_set = []
        startList = []
        task_available_start = timedelta(0)
        for tug in tugs:
            if tug in task.ori_task.tugs:
                continue
            if tug.type >= task.req_types[0]:
                available_start = max(max(task.start_time, tug.next_available_time)+count_move_time(tug.pos, task.start), task.start_time)
                startList.append([tug, available_start])
        
        if len(startList)!=0 and len(best_set)==0:
            opt = min(startList, key = lambda x: x[1])
            best_set.append(opt[0])
            task_available_start = opt[1] + timedelta(minutes=1)
        

        # 往上沒有符合型號的拖船，傳入的拖船型號沒有最高型號'type 0'
        if len(best_set)==0:
            # 往下派拖船型號
            startList = []
            for tug in tugs:
                if tug in task.ori_task.tugs:
                    continue
                if tug.type < task.req_types[0]:
                    available_start = max(max(task.start_time, tug.next_available_time)+count_move_time(tug.pos, task.start), task.start_time)
                    startList.append([tug, available_start])
            
            if len(startList)!=0 and len(best_set)==0:
                opt = min(startList, key = lambda x: x[1])
                best_set.append(opt[0])
                task_available_start = opt[1] + timedelta(minutes=1)
        
        # update jobs list of best set
        
        move_time = count_move_time(tug.pos, task.start)
        next_time = tug.next_available_time + move_time
        start_time_real = task_available_start 
        
        work_time = task.ori_task.start_time_real + task.ori_task.work_time - task.start_time
           
        # 更新原本已經派的tug的next_available_time
        for t in tugs:
            if t.tug in task.ori_task.tugs:
                t.next_available_time += max(start_time_real - task.start_time, timedelta(0)) 

        task.start_time = task_available_start
        nt = [task.start_time, task.start_time + work_time, task.start, task.to]
        check = False
        for tug in best_set:
            tug.jobs, check = insertjob(nt, tug, tug.jobs)
            # if check==True:
                # print('good insert',tug.id)
            for i in range(len(tugs)):
                if tugs[i].id == tug.id:
                    tugs[i].jobs = tug.jobs
            tug.next_available_time = task_available_start + work_time 
            # print('tug_next', tug.next_available_time)
            tug.pos = get_pier_latlng(task.to)

        if check==True:
            for t in tasks:
                if t.id == task.id:
                    t.tugs = [best.tug for best in best_set]
                    t.start_time = task.start_time
        # else: 
            # print('!!!!!error insert')

    

    '''--------處理拖船需求二以上---------'''
    for task in tasks_priority:
        stderr.write("Dispatching task {} \n".format(task.id))
        best_set = []
        delayList = []
        cands = candSet(task, tugs, 'over')
        opt_delay_time = timedelta(0)
        for cand in list(cands):
            delaytime = cal_delay(task, list(cand))
            
            if delaytime == timedelta(0):
                best_set.extend(list(cand))
                opt_delay_time = delaytime
                break
            delayList.append([list(cand), delaytime])
        
        if len(delayList)!=0 and len(best_set)==0:
            opt = min(delayList, key = lambda x: x[1])
            best_set.extend(opt[0])
            opt_delay_time = opt[1]
        

        # 往上沒有符合型號的拖船，傳入的拖船型號沒有最高型號'type 0'
        if len(best_set) == 0:
            # 往下派拖船型號
            delayList = []
            cands = candSet(task, tugs, 'every')
            for cand in list(cands):
                delaytime = cal_delay(task, list(cand))
                
                if delaytime == timedelta(0):
                    best_set.extend(list(cand))
                    opt_delay_time = delaytime
                    break
                delayList.append([list(cand), delaytime])
            
            if len(delayList)!=0 and len(best_set)==0:
                opt = min(delayList, key = lambda x: x[1])
                best_set.append(opt[0])
                opt_delay_time = opt[1]
            #

        # update jobs list of best set
        
        task.start_time = task.start_time + opt_delay_time
    
        nt = [task.start_time, task.start_time + predict_worktime(task, best_set), task.start, task.to]
        check = False
        for tug in best_set:
            tug.jobs, check = insertjob(nt, tug, tug.jobs)
            # if check==True:
                # print('good insert',tug.id)
            # else:
                # print('!!!!!error insert')
            for i in range(len(tugs)):
                if tugs[i].id == tug.id:
                    tugs[i].jobs = tug.jobs
                    

        if check==True:
            for t in tasks:
                if t.id == task.id:
                    t.tugs = [best.tug for best in best_set]
                    t.start_time = task.start_time
         
        
    '''----------處理拖船需求1---------'''
    for task in tasks_ones:
        stderr.write("Dispatching task {} \n".format(task.id))
        best_set = []
        delayList = []
        opt_delay_time = timedelta(0)
        for tug in tugs:
            # find tug with smallest delay
            if tug.type >= task.req_types[0]:
                delaytime = cal_delay(task, [tug])
                
                if delaytime == timedelta(0):
                    best_set.append(tug)
                    opt_delay_time = delaytime
                    break
                delayList.append([tug, delaytime])
        
        if len(delayList)!=0 and len(best_set)==0:
            opt = min(delayList, key = lambda x: x[1])
            best_set.append(opt[0])
            opt_delay_time = opt[1]
        

        # 往上沒有符合型號的拖船，傳入的拖船型號沒有最高型號'type 0'
        if len(best_set)==0:
            # 往下派拖船型號
            delayList = []
            for tug in tugs:
                if tug.type < task.req_types[0]:
                    delaytime = cal_delay(task, [tug])
                    if delaytime == timedelta(0):
                        best_set.append(tug)
                        opt_delay_time = delaytime
                        break
                    delayList.append([tug, delaytime])

            if len(delayList)!=0 and len(best_set)==0:
                opt = min(delayList, key = lambda x: x[1])
                best_set.append(opt[0])
                opt_delay_time = opt[1]

        
        # update jobs list of best set
        
        task.start_time = task.start_time + opt_delay_time
        
        nt = [task.start_time, task.start_time + predict_worktime(task, best_set), task.start, task.to]
        check = False
        for tug in best_set:
            tug.jobs, check = insertjob(nt, tug, tug.jobs)
            # if check==True:
                # print('good insert',tug.id)
            # else: 
                # print('!!!!!error insert')
            for i in range(len(tugs)):
                if tugs[i].id == tug.id:
                    tugs[i].jobs = tug.jobs

        if check==True:
            for t in tasks:
                if t.id == task.id:
                    t.tugs = [best.tug for best in best_set]
                    t.start_time = task.start_time
        
    

    return [task.tugs for task in tasks], [task.start_time for task in tasks]
