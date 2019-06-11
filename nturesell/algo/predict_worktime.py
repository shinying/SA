"""providing worktime prediction
"""

import numpy as np
import pandas as pd
from datetime import timedelta
from .outsourcing.WorkTimePrediction import WorkTimePrediction
from .port import get_pierToPier_dist, get_reverse


wpt = WorkTimePrediction()

def predict_worktime(task, tug_set):
    assert tug_set, "Empty tug list"
    df = dfCreator(task, tug_set)
    return (timedelta(minutes=wpt.run(df)[0]))


def classify_weight_level(ship_weight: int):
    level = {5000: 1, 10000: 2, 15000: 3,
             30000: 4, 45000: 5, 60000: 6, 100000: 7}
    for k in level:
        if ship_weight < k:
            return (level[k])
    return 8


def dfCreator(task, tug_set):
    port = 1 if task.start == 9001 else 2
    tug_cnt = len(tug_set)

    weight_lev = classify_weight_level(task.ship.weight)
    dist = get_pierToPier_dist(task.start, task.to)
    wind = 3
    reverse = get_reverse(task)

    # time
    time = task.start_time
    month = time.month
    weekday = time.weekday() + 1
    hour = time.hour

    # avg_hp
    avg_hp = 0
    mysum = 0
    for i in range(len(tug_set)):
        mysum = mysum + tug_set[i].hp
    avg_hp = mysum / len(tug_set)

    # create dataframe
    df = pd.DataFrame([[task.ship_state,
                        port,
                        tug_cnt,
                        task.ship.weight,
                        weight_lev,
                        dist,
                        wind,
                        task.side,
                        reverse,
                        month,
                        weekday,
                        hour,
                        avg_hp]],
                      columns=list(["sailing_status",
                                    "port",
                                    "tug_cnt",
                                    "total_weight",
                                    "weight_level",
                                    "dist",
                                    "wind",
                                    "park",
                                    "reverse",
                                    "month",
                                    "weekday",
                                    "hour",
                                    "avg_hp"]))
    return (df)
