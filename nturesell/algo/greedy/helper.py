import math
from datetime import datetime, timedelta
from random import randint, random
from itertools import combinations
import numpy as np
from ..model import TaskState, TugState, ShipState, ChargeTypeList, ChargeType
from ..port import get_pier_latlng
from ..settings import PENALTY, TUG_SPEED


def tug_to_ChargeType(tug_set):
    return([tug.type for tug in tug_set])

def classify_weight_level(ship_weight):
    level = {5000: 1, 10000: 2, 15000: 3,
            30000: 4, 45000: 5, 60000: 6, 100000: 7}
    for k in level:
        if ship_weight < k:
            return (level[k])
    return (8)

def find_required_tug(weight, tug_cnt):
    """
    Args:
        weight (TASK.ship.weight) : ship weight
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



def find_possible_set(tugs, required_tugs_list):
    """Find all combinations from currently available tugs

    Args:
        tugs ([TUG]): a list of available tugs
        required_tug_list ([ChargeType]): a list of required_tug_list

    Returns:
        possible_set ([(TUG)]): list of tuples of tugs
    """
    n = len(required_tugs_list)

    return list(combinations(tugs, n))

# 一組拖船組合是否有符合required_tug_list的派遣規則（篩選possible_set）
def max_arrival_time(task, tug_set):
    """Find the latest arrival time of a tug within a tug set

    Args:
        Task (TASK): a task
        tug_set ([TUG]): a list of tug

    Returns:
        max_arrival_time (datetime)
    """
    arv_time = [count_move_time(task.ship_state, tug.pos, task.start) + tug.next_available_time
                for tug in tug_set]
    return(max(arv_time))


def tug_to_charge_type(tug_set):
    return([tug.type for tug in tug_set])


def count_move_dis(state, start, to):
    """
    Args:
        state (TASK_STATE)
        start ((float, float)): latitide and longitude
        to (int): pier number

    Returns:
        km (float)
    """
    to = get_pier_latlng(to)
    dis = count_dis(float(start[0]), float(start[1]), float(to[0]), float(to[1]))
    return dis

def move_dis_to_time(dis: float, velo=TUG_SPEED) -> timedelta:
    return timedelta(minutes=((dis / 1.852) / (velo / 60)))

def count_move_time(state, start, to, velo=TUG_SPEED):
    """
    Args:
        state (TASK_STATE)
        start ((float, float))
        to (int)

    Returns:
        move_time (timedelta)
    """
    dis = count_move_dis(state, start, to)
    return move_dis_to_time(dis)


def count_dis(base_lat, base_lng, lat, lng):
    """Compute the  Euclidean distance

    Args:
        base_lat (float)
        base_lng (float)
        lat (float)
        lng (float)

    Returns:
        dist (float) scale: km
    """
    lon1, lat1, lon2, lat2 = map(math.radians, [base_lng, base_lat, lng, lat])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2) ** 2 + math.cos(lat1) * \
        math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371
    return c * r


def get_oil_price(hp):
    """
    Arg:
        hp (int): horsepower of tugs

    Return:
        price (float): oil price ($/km)
    """
    hp_price = {
        1800: 134.1075498270909,
        2400: 185.0696699493183,
        3200: 257.887743955886,
        3300: 267.3812284262817,
        3400: 276.9616518343608,
        3500: 286.6290141801232,
        3600: 296.3833154635688,
        4000: 336.2699099741844,
        4200: 356.734840855592,
        4400: 377.5475274877326,
        4500: 388.0842792103279,
        5200: 464.2758315236272,
        6400: 604.8009600994644,
    }
    return hp_price[hp]


def count_profit(Task, tug_set, work_time, arrival_time):
    """
    Args:
        Task (TASK)
        tug_set ([TUG])
        work_time (timedelta)
        arrival_time (datetime)
    Returns:
        total_profit (int): the total profit of this pair
    """
    total_moving_cost = 0
    total_revenue = 0
    required_tug_set = find_required_tug(Task.ship.weight, Task.tug_cnt)


    charge = ChargeType_to_price(tug_set, required_tug_set)

    for i in range(len(tug_set)):
        # move_time.append(count_move_time(Task.ship_state, tug_set[i].pos, Task.start))
        move_dis = count_move_dis(Task.ship_state, tug_set[i].pos, Task.start)
        move_time = move_dis_to_time(move_dis)

        if move_time + work_time < timedelta(minutes=60): # less than an hour
            total_revenue += charge[i]
        else: # over an hour, count the number of 30 mins
            time = (math.ceil(((move_time+work_time-timedelta(minutes=60)).seconds / 60) / 30)
                   * 30 + 60)
            total_revenue += (charge[i] * time / 60)
        total_moving_cost += get_oil_price(tug_set[i].hp) * move_dis
    ## add tug count profit
    add_revenue,add_moving_cost = 0,0
    if Task.add_tug:
        add_revenue,add_moving_cost = add_tug_profit_count(Task)
    total_moving_cost += add_moving_cost
    total_revenue += add_revenue

    delay_time = 0 if arrival_time <= Task.start_time \
                else ((arrival_time - Task.start_time).seconds / 60)
    total_waiting_cost = PENALTY * delay_time
    total_profit = total_revenue - total_moving_cost - total_waiting_cost
    return ({"total_revenue": total_revenue, 
            "total_waiting_cost": total_waiting_cost,
            "total_moving_cost": total_moving_cost,
            "total_profit": total_profit})


def ChargeType_to_price(tug_list, required_tug_list):
    price = []
    tug_list = sorted(tug_list, key=(lambda tug: tug.type))
    required_tug_list.sort()
    price_dict = {117: 7395, 118: 10846, 119: 19720, 120: 22310, 130: 32000}
    for i in range(len(tug_list)):
        try:
            price.append(
                min(price_dict[required_tug_list[i]], price_dict[tug_list[i].type]))
        except:
            price.append(price_dict[tug_list[i].type])
    return price

def add_tug_profit_count(task):
    price_dict = {117: 7395, 118: 10846, 119: 19720, 120: 22310, 130: 32000}
    revenue = 0
    moving_cost = 0
    for i in task.add_tug:
        move_dis = count_move_dis(task.ship_state, i.tug.pos, task.start)
        add_time = (task.start_time + task.work_time - i.start_moving_time)
        if add_time <= timedelta(60):
            revenue += price_dict[i.tug.type]
        else:
            revenue += price_dict[i.tug.type] * math.ceil(add_time/60)
        moving_cost += get_oil_price(i.tug.hp) * move_dis
    return(revenue,moving_cost)

def showdetails(tasks, method, verbose=False):
    tasks.sort(key=(lambda task: task.id))
    revenue = 0
    waiting_cost = 0
    moving_cost = 0
    profit = 0
    for task in tasks:
        max_tug_arrival = max_arrival_time(task, task.tugs)
        info = count_profit(task, task.tugs, task.work_time, max_tug_arrival)
                            
        if verbose:
            task.show()
            print("* Required Tugs:", end=" ")
            print([i.value for i in find_required_tug(task.ship.weight, task.tug_cnt)])
            print("* Dispatched Tugs:", end=" ")
            print([i.value for i in tug_to_ChargeType(task.tugs)])
            print("")
            print("* Revenue: {:.2f}\n* Waiting_cost: {:.2f} \n* Moving_cost: {:.2f}\n* Profit: {:.2f}\n".format(
                info['total_revenue'], task.delay_time.seconds/60 * PENALTY,
                info['total_moving_cost'], info['total_profit']))
        revenue += info['total_revenue']
        waiting_cost += task.delay_time.seconds / 60
        moving_cost += info['total_moving_cost']
        profit += info['total_revenue']

    print("======== {}_SUMMARY ========".format(method))
    print("Revenue: {:.2f}\nTotal_waiting_cost: {:.2f}\nTotal_moving_cost: {:.2f}\nProfit: {:.2f}".format(
        revenue, waiting_cost, moving_cost, profit-waiting_cost-moving_cost))