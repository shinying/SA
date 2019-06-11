import numpy as np
import random
import copy
import plotly.tools as pt
import plotly.plotly as pp
import plotly.figure_factory as ff
from datetime import datetime, timedelta
from collections import deque
# pt.set_credentials_file(username='hanjuTsai', api_key='XEOnjaC9Om7WcOwgbRqs')

pt.set_credentials_file(username='angyeahyeah6',
                        api_key='heDVJdzx2KYVJAfpReWi')

number_of_colors = 100
color = ["#"+''.join([random.choice('0123456789ABCDEF')
                      for j in range(number_of_colors)]) for i in range(number_of_colors)]


def ganttplot(tasks, tugs):
    colors = dict()
    for task in tasks:
        #     color = "rgb({}, {}, {})".format(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        color = 'rgb(128, 138, 135)'
        colors[str(task.id)] = color
    colors['delay_time'] = 'rgb(255,153,51)'
    colors['move_time'] = 'rgb(0,204,204)'
    colors['work_time'] = 'rgb(128, 138, 135)'

    df = []
    tasks.sort(key=lambda x: x.start_time_real)
    for task in tasks:
        df.append(dict(Task=str(task.id), Start=task.start_time_real,
                       Finish=task.start_time_real + task.work_time, Resource=str(task.id)))
        df.append(dict(Task=str(task.id), Start=task.start_time,
                       Finish=task.start_time_real, Resource='delay_time'))

    fig = ff.create_gantt(df, colors=colors, index_col='Resource',
                          show_colorbar=True, group_tasks=True)
    pp.plot(fig, filename='task-gantt', world_readable=True)

    df = []
    for tug in tugs:
        ts = copy.copy(tug.ts)
        while ts:
            move = ts.popleft()
            start = ts.popleft()
            end = ts.popleft()
            df.append(dict(Task=str(tug.tug_id), Start=move,
                           Finish=start, Resource='move_time'))
            df.append(dict(Task=str(tug.tug_id), Start=start,
                           Finish=end, Resource='work_time'))
            
    
    fig = ff.create_gantt(df, group_tasks=True, show_colorbar=True,
                          colors=colors, index_col='Resource', showgrid_x=True)
    pp.plot(fig, filename='tug-worktime-gantt', world_readable=True)
