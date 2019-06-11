import random
from enum import Enum, IntEnum
from enum import Enum

from faker import Faker
from faker_enum import EnumProvider
from datetime import timedelta

from model import Ship, Task, Tug, ShipState, TaskState, TugState, Side
from test import lon_lat_list, tug_list, system_time

fake = Faker()
fake.add_provider(EnumProvider)

def test_ship(data_num):
    ship_list = []
    for i in range(data_num):
        ran_lon_lat = random.randint(0, len(lon_lat_list)-1)
        ship_list.append(Ship(ship_id=random.randint(10000, 99999),
                            cur_pos=(lon_lat_list[ran_lon_lat][0], lon_lat_list[ran_lon_lat][1]),
                            weight=random.randint(2000, 120000)))
    return(ship_list)


def test_tug():
    result = []
    for i in range(len(tug_list)):
        ran_lon_lat = random.randint(0, len(lon_lat_list)-1)
        result.append(Tug(tug_id=i,
                        cur_pos = (lon_lat_list[ran_lon_lat][0], lon_lat_list[ran_lon_lat][1]),
                        charge_type=tug_list[i][2],
                        hp = tug_list[i][1],
                        state = fake.enum(TugState)))
    return(result)


def test_task(ship_list):
    data_num = random.randint(0, len(ship_list))
    task_list = []
    time_list = [system_time + timedelta(minutes=random.randint(10, 200)), system_time + timedelta(
        minutes=random.randint(10, 200)), system_time + timedelta(minutes=random.randint(10, 200))]
    time_list = sorted(time_list)
    state = [ShipState.IN, ShipState.OUT, ShipState.TRANSFER]

    for i in range(data_num):
        s = ship_list[i]
        for j in range(len(time_list)):
            ran_lon_lat = random.randint(0, len(lon_lat_list)-1)
            task_list.append(Task(i=i,
                                  ship=s,
                                  ship_state=state[j],
                                  task_state=TaskState.UNPROCESSED_UNASSIGNED,
                                  start_time=time_list[j],
                                  start=(lon_lat_list[ran_lon_lat][0], lon_lat_list[ran_lon_lat][1]),
                                  dest=(lon_lat_list[ran_lon_lat][0], lon_lat_list[ran_lon_lat][1]),
                                  side=fake.enum(Side)))

    return(task_list)
