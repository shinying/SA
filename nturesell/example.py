from typing import List
from datetime import datetime
from algo.estimator import Estimator
from algo.model import Task, Tug


def my_dispatch(tasks: List[Task], tugs: List[Tug], sys_time: datetime) -> List[List[Tug]]:
    """
    Args:
        tasks: tasks to be dispatched
        tugs: tugs currently available
        sys_time: current time in simulator

    Returns:
        a list of lists of tugs in the same order as the given tasks
        a list of expected starting time of the tasks

    Notes:
        Please implement your own dispatching algorithm with the given input and output format
        Avoid directly modifing attributes of tasks and tugs
    """

    # TODO: dispatch all tasks
    lists_of_tugs = [[]]
    start_times = []

    return lists_of_tugs, start_times


def estimate_my_algorithm():
    """
    The way to estimate your algorithm
    """
    est = Estimator()
    result = est.run(my_dispatch)
    result = est.run_hist()
    # est.multi_run([], sample_size, benchmark, verbose)
    # If detailed information of tasks is needed
    est.print_result(result, verbose=True)
    # est.draw(result)
    

# # # Example # # # 

def estimate_example():
    """
    An example to estimate the build-in dispatching algorithm
    See cool_dispatch in algo/greedy/cool.py for reference
    """
    est = Estimator()
    from algo.greedy.cool import cool_dispatch
    from algo.greedy.efficient import efficient_dispatch
    est.set_range(100, 120)
    # est.pick_day('least')
    kh = est.run(cool_dispatch, verbose=False)
    # result = est.run_hist()
    # print(est.multi_run([cool_dispatch, efficient_dispatch], 3))
    est.print_result(kh)
    # est.print_result(result, verbose=False, split_profit=True)
    est.draw(kh['sum'])

estimate_example()
