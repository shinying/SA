from .simulator import Simulator
from .model import Company
from .his.data import get_data, df
from .utils.plot import ganttplot
from .utils.utility import count_move_dis, move_dis_to_time, get_pier_latlng, get_oil_price
from copy import deepcopy
from collections import deque
from datetime import datetime, timedelta
from sys import stderr
from time import strftime, time
from scipy import stats
import numpy as np
import pandas as pd
import random

class Estimator():
    """A class to estimate the given dispatching algorithm

    Methods: 
        run: estimates the algorithm with randomly generated events 
    """
    def __init__(self):
        self.row_start = 100
        self.row_end = 120
        self.pg_bar = 20

    def set_range(self, start, end):
        """Specify the range in history data for estimation
        
        Args:
            start (int): starting row of his/2017.xlsx
            end (int): ending row of his/2017.xlsx
        """
        assert end-start > 0, "Negative range"
        self.row_start = start
        self.row_end = end

    def pick_day(self, day):
        """Set the range to the day with the most or least tasks

        Args:
            day (str): one of 'most' or 'least'
        """

        picks = ['most', 'least','median','mean', '30days']
        if day not in picks:
            raise ValueError("Invalid day. Expected one of {}.".format(picks))
        date = df.start_time.apply(lambda x : x.date())
        all_dates = np.unique(date)
        date_num = np.array([])
        for i in all_dates:
            num = np.count_nonzero(date == i)
            date_num = np.append(date_num, num)
        
        if day == picks[0]:
            max_row = np.where(date == all_dates[date_num.argmax()])
            self.row_start = max_row[0].min()
            self.row_end = max_row[0].max()
        elif day == picks[1]:
            min_row = np.where(date == all_dates[date_num.argmin()])
            self.row_start = min_row[0].min()
            self.row_end = min_row[0].max()
        elif day == picks[2]:
            median_row = np.where(date == all_dates[np.argsort(date_num)[len(date_num)//2]])
            self.row_start = median_row[0].min()
            self.row_end = median_row[0].max()
        elif day == picks[3]:
            mean = np.mean(date_num)
            mean_idx = (np.abs(date_num-mean)).argmin()
            mean_row = np.where(date == all_dates[mean_idx])
            self.row_start = mean_row[0].min()
            self.row_end = mean_row[0].max()
        elif day == picks[4]:
            days = [datetime(2017, 1, 1).date() + timedelta(random.randint(1,365) - 1)  for i in range(0,30)]
            output = []
            start_days = []
            end_days = []
            print('Picked dates:')
            for pickday in days:
                print(pickday)
                day_idx = [i for i, date in enumerate(date) if date == pickday]
                if len(day_idx) == 0:
                    days.append(datetime(2017, 1, 1).date() + timedelta(random.randint(1,365) - 1))
                    continue
                start = min(day_idx)
                end = max(day_idx)
                start_days.append(start)
                end_days.append(end)
                output.append((start, end))  

            self.row_start = start_days
            self.row_end = end_days

            return start_days, end_days



    def run(self, algorithm, verbose=False, divided=False):
        """
        Arg:
            algorithm (function): The algorithm as a python function to be estimated

        Return:
            result (dict): The result of estimation containing waiting times, tugs, profit, etc
        """
        
        t_start = time()
        self.tasks, self.tugs = get_data(self.row_start, self.row_end)
        if verbose:
            print("Simulation with {} tasks".format(len(self.tasks)))

        if divided:
            kh_tugs = [tug for tug in self.tugs if tug.company is Company.KHPORT]
            kh_tasks = [task for task in self.tasks if task.company is Company.KHPORT]
            gc_tugs = [tug for tug in self.tugs if tug.company is Company.GANGCHIN]
            gc_tasks = [task for task in self.tasks if task.company is Company.GANGCHIN]

            kh_res = Simulator(kh_tasks, deepcopy(kh_tugs), deepcopy(gc_tugs), \
                Company.KHPORT, verbose).run(algorithm)
            gc_res = Simulator(gc_tasks, deepcopy(gc_tugs), deepcopy(kh_tugs), \
                Company.GANGCHIN, verbose).run(algorithm)
            
            t_end = time()
            kh_res['algorithm'] = algorithm
            kh_res['time_usage'] = t_end - t_start
            return kh_res, gc_res
            # return kh_res
            
        else:
            for i in self.tugs:
                print(i)
            simulator = Simulator(self.tasks, self.tugs, verbose=verbose)
            result = simulator.run(algorithm)
            t_end = time()

            result['algorithm'] = algorithm
            result['time_usage'] = t_end - t_start

            return result

    def run_hist(self, divided=True):
        tasks, _ = get_data(self.row_start, self.row_end, from_hist=True)
        for task in tasks:
            task.tugs.sort(key=lambda tug: tug.tug_id)
            for tug in task.tugs:
                move_dis = count_move_dis(tug.pos, task.start)
                move_time = move_dis_to_time(move_dis)
                task.moving_time += move_time
                task.moving_cost += get_oil_price(tug.hp) * move_dis
                task.tugs_start_time.append(task.start_time_real-move_time)
                tug.pos = get_pier_latlng(task.to)

        def history():
            pass

        if divided:
            kh_tasks = [task for task in tasks if task.company is Company.KHPORT]
            gc_tasks = [task for task in tasks if task.company is Company.GANGCHIN]
            kh_sim = Simulator(kh_tasks, [], subject=Company.KHPORT)
            gc_sim = Simulator(gc_tasks, [], subject=Company.GANGCHIN)
            for sim in [kh_sim, gc_sim]:
                sim.collect_result()
                sim.result['algorithm'] = history
                sim.result['time_usage'] = 0
            return kh_sim.result, gc_sim.result
        else:
            sim = Simulator(tasks, [])
            sim.collect_result()
            sim.result['algorithm'] = history
            sim.result['time_usage'] = 0
            return sim.result

    def multi_run(self, algorithms, n=30, benchmark='profit', divided=True, with_hist=False, \
        verbose=False, seed=None):
        """
        Args:
            algorithms ([function]): a list of funcionts to be estimated
            n (int): the number of samples to estimate an algorithm
            benchmark (str): estimation targets between algorithms, one of 'profit', 
                'revenue', 'waiting_cost', 'waiting_time', 'moving_cost', 'moving_time',
                'matched', 'oversize', 'undersize'
            with_hist (bool): whether to include comparison with historical result
            verbose (bool): whether to print detailed process of simulation
            seed (int): random seed

        Return:
            pandas.DataFrame: a dict with keys being algorithms' names and values being n times results
        """

        assert len(algorithms), "The list of algorithms to be estimated is empty"
        assert n > 0, "Negative simulation times"
        bms = ['profit', 'revenue', 'waiting_cost', 'waiting_time', 'moving_cost', 
            'moving_time', 'matched', 'oversize', 'undersize']
        if benchmark not in bms:
            raise ValueError("Invalid benchmark. Expected one of {}.".format(bms))
        if not seed:
            seed = datetime.now().microsecond

        self.tasks, self.tugs = get_data(self.row_start, self.row_end)
        if divided:
            kh_tasks = [task for task in self.tasks if task.company is Company.KHPORT]
            gc_tasks = [task for task in self.tasks if task.company is Company.GANGCHIN]
            kh_tugs = [tug for tug in self.tugs if tug.company is Company.KHPORT]
            gc_tugs = [tug for tug in self.tugs if tug.company is Company.GANGCHIN]
            
            assert (kh_tugs is not None) or (gc_tugs is not None), 'do not have any tugs of this company'
            
            kh_samples = {}
            gc_samples = {}
            times = deque([])
            for algo in algorithms:
                print("Estimating {}...".format(algo.__name__), end="")
                kh_values = []
                gc_values = []
                if not verbose:
                    self._print_progress_init()
                else:
                    print("")

                random.seed(seed)
                t_start = time()

                for i in range(n):
                    if verbose: print("Round {}/{}...".format(i+1, n))

                    kh_sim = Simulator(deepcopy(kh_tasks), deepcopy(kh_tugs), deepcopy(gc_tugs),
                        Company.KHPORT, verbose)
                    kh_values.append(kh_sim.run(algo)['K'][benchmark])
                    gc_sim = Simulator(deepcopy(gc_tasks), deepcopy(gc_tugs), deepcopy(kh_tugs),
                        Company.GANGCHIN, verbose)
                    gc_values.append(gc_sim.run(algo)['G'][benchmark])

                    if not verbose: self._print_progress_done(i, n)

                t_end = time()
                if not verbose: print('')
                kh_samples[algo.__name__] = kh_values
                gc_samples[algo.__name__] = gc_values
                times.append(t_end-t_start)

            if with_hist:
                kh_his, gc_his = self.run_hist()
                kh_samples['history'] = kh_his['sum'][benchmark] 
                gc_samples['history'] = gc_his['sum'][benchmark]
                times.append(0)

            print("\n=== Simulation Result (KHPORT) ===")
            self._print_multi(kh_samples)
            print("\n=== Simulation Result (GANGCHIN) ===")
            self._print_multi(gc_samples, times)

            if not with_hist:
                print("# # T Test (KHPORT) # #")
                print(self.compare(kh_samples))
                print("# # T Test (GANGCHIN) # #")
                print(self.compare(gc_samples))
                return kh_samples, gc_samples

        else:
            samples = {}
            times = deque([])
            for algo in algorithms:
                print("Estimating {}...".format(algo.__name__), end="")
                values = []
                if not verbose: self._print_progress_init()
                else: print("")
                random.seed(seed)

                t_start = time()
                for i in range(n):
                    if verbose:
                        print("Round {}/{}...".format(i+1, n))
                    simulator = Simulator(deepcopy(self.tasks), deepcopy(self.tugs), verbose)
                    values.append(simulator.run(algo)['sum'][benchmark])

                    if not verbose:
                        self._print_progress_done(i, n)
                t_end = time()
                if not verbose: print('')
                samples[algo.__name__] = values
                times.append(t_end-t_start)
            
            if with_hist:
                samples['history'] = self.run_hist(divided=False)['sum'][benchmark]
                times.append(0)

            print("\n=== Simulation Result ===")
            self._print_multi(samples, times)
            
            if not with_hist:
                print(self.compare(samples))

    def _print_multi(self, samples, times=None):
        for algo, result in samples.items():
            print("Algorithm:", algo)
            print("Mean:", round(np.mean(result), 2))
            print("Std:", round(np.std(result), 2))
            if times:
                print("Time: ", round(times.popleft(), 4), 's')
            print("")
            one_sample_ttest = stats.ttest_1samp(result, samples["history"])
            print("T-test result: ",one_sample_ttest)
        
    def compare(self, samples):
        """
        Arg:
            samples (dict): a dict with keys being algorithms' names 
                and values being n times results from multi_run()
        Return:
            pandas.DataFrame: a table of p-value
        """
        N = len(samples)
        result = np.zeros((N, N))
        name = list(samples.keys())
        for i in range(N-1):
            for l in range(i+1, N):
                _, pvalue = stats.ttest_rel(samples[name[i]],samples[name[l]])
                result[i][l] = pvalue
                result[l][i] = pvalue
        matrix = pd.DataFrame(result)
        matrix.columns = name
        matrix.index = name
        return matrix

    def print_result(self, result, result2=None, verbose=False, split_profit=True):
        """
        Args:
            result (Dict): Estimation result generated by run().
            verbose (bool): True to print detail information about tasks, False for summary
        """
        if not result:
            print("Printing Error: No result", file=stderr)
            return
        
        print(("\n"+"="*42+"\n="+"Simulation Result of {}" \
        .center(42-len(result["algorithm"].__name__))+"=\n"+"="*42+"\n") \
        .format(result["algorithm"].__name__.upper()))

        
        i = 1
        while i <= 2:
            if result2:
                print("# # # # # # Result {} # # # # # #\n".format(i))
            if verbose:
                self._print_tasks(result['sum']['tasks'])
            if 'K' in result:
                self._print_company(result)
            self._print_summary(result['sum'])
            if result2:
                i += 1
                result = result2
            else:
                break 


        print("• Time usage: {:.2f} secs".format(result['time_usage']))
        print("• Time per call: {:.2f} secs\n".format(
            result['time_usage']/result['sum']['n_calls']))
    
    def _print_tasks(self, tasks):
        tasks.sort(key=lambda task: task.id)
        for task in tasks:
            print("=========== Task {} Result ===========".format(task.id))
            print(("* Ship ID: {}\n" +
                "* Ship State: {}\n" +
                "* Should Started at: {}\n" +
                "* Actually Started at: {}\n" +
                "* Working time: {:02d}:{:02d}\n" +
                "* State: {}\n" +
                "* Weight: {}\n" +
                "* Task Company: {}\n\n" +  
                "* Required types: {}\n" +
                "* Dispatched types: {}\n" +
                "* Dispatched tugs: {}\n").format(
                    task.ship.ship_id,
                    task.ship_state.name,
                    task.start_time.strftime("%Y-%m-%d %H:%M"),
                    task.start_time_real.strftime("%Y-%m-%d %H:%M"),
                    task.work_time.seconds//3600, (task.work_time.seconds%3600)//60, 
                    task.task_state.name,
                    task.ship.weight,
                    task.company.name,
                    [t.name for t in task.req_types],
                    [t.type.name for t in task.tugs],
                    [str(t.tug_id) + '(' + t.company.value + ')' for t in task.tugs],
                ))
            if task.tmp_need_time:
                print("* Temp need time: {}\n".format(
                    task.tmp_need_time.strftime("%Y-%m-%d %H:%M")))
                    
            print(("* Revenue: {:.2f}\n" + 
                "* Waiting time: {:02d}:{:02d}\n" +
                "* Waiting cost: {:.2f} \n" +
                "* Moving time: {:02d}:{:02d}\n" +
                "* Moving cost: {:.2f}\n" +
                "* Profit: {:.2f}\n").format(
                    task.revenue,
                    task.waiting_time.seconds//3600, (task.waiting_time.seconds%3600)//60, 
                    task.waiting_cost,
                    task.moving_time.seconds//3600, (task.moving_time.seconds%3600)//60, 
                    task.moving_cost,
                    task.profit,
                ))

    def _print_company(self, result):
        for name, c in Company.__members__.items():
            print("====== Company " + name + " ======\n")
            print(("• Revenue: {:.4f}\n" +
            "• Moving cost: {:.4f}\n" +   
            "• Moving time: {:02d}:{:02d}\n" +
            "• Profit: {:.4f}\n" +
            "• Managing_revenue: {:.4f}\n" ).format(
            result[c.value]['revenue'], 
            result[c.value]['moving_cost'],
            result[c.value]['moving_time'].seconds//3600,
            (result[c.value]['moving_time'].seconds%3600)//60, 
            result[c.value]['profit'],
            result[c.value]['managing_revenue']))

    def _print_summary(self, result):
        print("============== Summary =================\n")
        print(("• Revenue: {:.4f}\n" +
                "• Waiting_cost: {:.4f}\n" +
                "• Waiting_time: {:02d}:{:02d}\n" +
                "• Moving_cost: {:.4f}\n" + 
                "• Moving_time: {:02d}:{:02d}\n" +
                "• Matched: {:.2%}\n" +
                "• Oversized: {:.2%}\n" +  
                "• Undersized: {:.2%}\n" +   
                "• Profit: {:.4f}\n").format(
                result["revenue"], 
                result["waiting_cost"], 
                result["waiting_time"].seconds//3600, 
                (result["waiting_time"].seconds%3600)//60,
                result["moving_cost"],
                result["moving_time"].seconds//3600,
                (result["moving_time"].seconds%3600)//60,
                result['matched'],
                result['oversize'],
                result['undersize'],
                result["profit"],))


    def _print_progress_init(self):
        print('|'+'-'*self.pg_bar+'|', end='', flush=True)

    def _print_progress_done(self, done, leng):
        n = min((done+1)*self.pg_bar//leng, self.pg_bar)
        print('\b'*(self.pg_bar+1)+'█'*n+'-'*(self.pg_bar-n)+'|', end='', flush=True)

    def draw(self, result):
        if not result:
            print("Drawing Error: No result", file=stderr)
            return
        if 'sum' in result:
            result = result['sum']
            ganttplot(result['tasks'], result['tugs'])

    
    
