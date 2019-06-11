import math
from datetime import datetime, timedelta
from random import randint
from itertools import combinations
from typing import List

from ..model import TaskState, TugState, ShipState, ChargeTypeList, Tug, Task, Ship, ChargeType
from ..port import get_pier_latlng
from ..settings import PENALTY, TUG_SPEED
from .cutil import c_move_dis_to_time, c_count_dis
from typing import Union

def count_move_dis(start, to):
    """Calculate moving distance from a coordinate to a pier

    Args:
        start ((float, float)): latitide and longitude
        to (int): pier number

    Returns:
        (float): distance in km
    """
    dest = get_pier_latlng(to)
    dis = count_dis(float(start[0]), float(start[1]), float(dest[0]), float(dest[1]))
    return dis


def move_dis_to_time(dis, velo=TUG_SPEED):
    """Convert moving distance to time
    """
    return timedelta(hours=c_move_dis_to_time(dis, velo))


def count_move_time(start, to, velo=TUG_SPEED):
    """Calculate moving time from a coordinate to a pier

    Args:
        start ((float, float))
        to (int)

    Returns:
        (timedelta): moving time
    """
    dis = count_move_dis(start, to)
    return move_dis_to_time(dis)


def count_dis(base_lat, base_lng, lat, lng):
    """Calculate the Euclidean distance

    Args:
        base_lat (float)
        base_lng (float)
        lat (float)
        lng (float)

    Returns:
        (float): distance in km
    """
    return c_count_dis(base_lng, base_lat, lng ,lat)


def get_oil_price(hp):
    """Provide oil cost per km from horsepower

    Arg:
        hp (int): horsepower of tugs

    Return:
        (float): oil price ($/km)
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


def get_prices(req_types, tugs):
    """Convert types of tugs to revenue per hour according to comparison 
    between required types and dispatched tugs

    Args:
        req_types ([ChargeType]): a list of required types of a task
        tugs ([Tug]): a list of tugs assigned to a task

    Return:
        ([int]): a list of prices ($/hour)
    """

    assert len(req_types) <= len(tugs)
    table = {117: 7395, 118: 10846, 119: 19720, 120: 22310, 121: 32000}
    req_types.sort()
    tugs.sort(key=lambda tug: tug.type)
    
    prices = []
    i = 0
    while i < len(req_types):
        prices.append(table[min(req_types[i], tugs[i].type)])
        i += 1
    while i < len(tugs):
        prices.append(table[tugs[i].type])
        i += 1
    return prices


def calculate_revenue(times: List[timedelta], req_types: List[ChargeType], tugs: List[Tug]) -> Union[float, list]:
    """Calculate revenue for a dispatched task

    Args:
        times ([timedelta]): a list of timestamps when the tugs started moving
        req_types ([ChargeType]): a list of required types for a task
        tugs ([Tug]): a list of tugs assigned to a task
        sep (bool): to separate profit between tugs

    Return:
        (float): revenue or ([float]): list of revenue

    """

    if not (len(times) and len(req_types) and len(tugs)):
        return 0
    
    assert len(times) == len(req_types) and len(times) == len(tugs), "Lists length differ"

    revenue = 0
    prices = get_prices(req_types, tugs)

    for time, price in zip(times, prices):
        cycles = math.ceil((time - timedelta(minutes=60)).seconds / 60 / 30) * 0.5 + 1 \
            if time > timedelta(minutes=60) else 1
        revenue += price * cycles
    return revenue


