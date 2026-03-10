import os
import sys
import tkinter as tk
from tkinter import ttk
from tkinter.ttk import Style

import pandas as pd
import matplotlib.pyplot as plt

sys.path.append(os.path.relpath("First-Come-First-Serve-scheduling"))
sys.path.append(os.path.relpath("Priority-Scheduling"))
sys.path.append(os.path.relpath("Round-Robin-scheduling"))
sys.path.append(os.path.relpath("Shortest-Job-First-scheduling"))
sys.path.append(os.path.relpath("WOA-Dynamic-Round-Robin-scheduling"))

from RR import simulate_rr_algorithm
from priority_p import simulate_priority_p_algorithm
from WOADRR import woa_optimize_assignment_quantum, simulate_rr_algorithm
from Hybrid_RR import simulate_hrr_algorithm
from RRSJF import simulate_rrsjf_algorithm


class tkinterApp(tk.Tk):

    # __init__ function for class tkinterApp
    def __init__(self, *args, **kwargs):
        # __init__ function for class Tk
        tk.Tk.__init__(self, *args, **kwargs)

        style = Style()
        style.configure('TButton',
                        background='blue',
                        foreground='white',
                        font=('Arial', 20, 'bold'),
                        borderwidth='4')

        style.configure('TLabel',
                        background='#081547',
                        foreground='white',
                        font=('Arial', 20, 'bold'),
                        borderwidth='4')

        style.map('TButton',
                  foreground=[('active', '!disabled', 'black')],
                  background=[('active', 'yellow')])
        # creating a container
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # initializing frames to an empty array
        self.frames = {}

        # iterating through a tuple consisting
        # of the different page layouts
        for F in (StartPage, RR, PriorityP, HRR, RRSJF, Chart, WOADRR):
            frame = F(container, self)

            # initializing frame of that object from
            # startpage, page1, page2 respectively with
            # for loop
            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(StartPage)

    # to display the current frame passed as
    # parameter
    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()


class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.config(bg='#081547')

        label = ttk.Label(self, text="CPU Scheduling algorithms simulator", font=LARGE_FONT)
        label.place(x=0, y=0)

        button4 = ttk.Button(self, text="RR", command=lambda: controller.show_frame(RR))
        button4.place(x=50, y=100)

        button6 = ttk.Button(self, text="Priority P", command=lambda: controller.show_frame(PriorityP))
        button6.place(x=50, y=200)

        button9 = ttk.Button(self, text="HRR", command=lambda: controller.show_frame(HRR))
        button9.place(x=50, y=300)

        button10 = ttk.Button(self, text="RRSJF", command=lambda: controller.show_frame(RRSJF))
        button10.place(x=50, y=400)

        button7 = ttk.Button(self, text="Chart", command=lambda: controller.show_frame(Chart))
        button7.place(x=300, y=200)

        button8 = ttk.Button(self, text="WOA-DRR", command=lambda: controller.show_frame(WOADRR))
        button8.place(x=300, y=300)


def print_result(root, result):
    label = ttk.Label(root, text=f"Number of processes = {result['n']}", font=LARGE_FONT, foreground='yellow')
    label.place(x=20, y=100)
    label = ttk.Label(root, text=f"Throughput = {result['throughput']}", font=LARGE_FONT, foreground='yellow')
    label.place(x=20, y=150)
    label = ttk.Label(root, text=f"CPU utilization = {result['cpu_util']}", font=LARGE_FONT, foreground='yellow')
    label.place(x=20, y=200)
    label = ttk.Label(root, text=f"Average waiting time = {result['awt']}", font=LARGE_FONT, foreground='yellow')
    label.place(x=20, y=250)
    label = ttk.Label(root, text=f"Average turn around time = {result['att']}", font=LARGE_FONT, foreground='yellow')
    label.place(x=20, y=300)
    label = ttk.Label(root, text=f"Average response time = {result['art']}", font=LARGE_FONT, foreground='yellow')
    label.place(x=20, y=350)


def set_data_for_chart(result):
    awt_arr.append(float(result['awt']))
    att_arr.append(float(result['att']))
    art_arr.append(float(result['art']))


class RR(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.config(bg='#081547')
        label = ttk.Label(self, text="Round-Robin algorithm:", font=LARGE_FONT)
        label.grid(row=0, column=4, padx=10, pady=10)

        result = simulate_rr_algorithm(data, 1)
        set_data_for_chart(result)
        print_result(self, result)

        button1 = ttk.Button(self, text="Back", command=lambda: controller.show_frame(StartPage))
        button1.place(x=20, y=450)




class PriorityP(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.config(bg='#081547')
        label = ttk.Label(self, text="Priority preemptive algorithm:", font=LARGE_FONT)
        label.grid(row=0, column=4, padx=10, pady=10)

        result = simulate_priority_p_algorithm(data)
        set_data_for_chart(result)
        print_result(self, result)

        button1 = ttk.Button(self, text="Back", command=lambda: controller.show_frame(StartPage))
        button1.place(x=20, y=450)


class Chart(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.config(bg='#081547')
        label = ttk.Label(self, text="Chart:", font=LARGE_FONT)
        label.grid(row=0, column=4, padx=10, pady=10)
        # Ensure WOA-DRR results are included only once
        if len(awt_arr) == 4:  # Only add if not already present
            from WOADRR import woa_optimize_assignment_quantum, simulate_rr_algorithm
            processes = [{"pid": row["process_id"], "burst_time": row["burst_time"]} for _, row in data.iterrows()]
            num_processors = 2
            quantum_min = 1
            quantum_max = 5
            population_size = 10
            max_iter = 30
            best_whale, best_fitness, progress = woa_optimize_assignment_quantum(
                processes, num_processors=num_processors, quantum_min=quantum_min, quantum_max=quantum_max,
                population_size=population_size, max_iter=max_iter, random_seed=42, verbose=False
            )
            assignment, quantums = best_whale
            processor_queues = [[] for _ in range(num_processors)]
            for i, proc in enumerate(assignment):
                processor_queues[proc].append(processes[i])
            # Average the metrics across all processors
            metrics_list = []
            for idx, queue in enumerate(processor_queues):
                if queue:
                    queue_df = pd.DataFrame({
                        'process_id': [t['pid'] for t in queue],
                        'burst_time': [t['burst_time'] for t in queue]
                    })
                    result = simulate_rr_algorithm(queue_df, quantums[idx], verbose=False, woa_label=True)
                    metrics_list.append(result)
            if metrics_list:
                awt_arr.append(sum(float(m['awt']) for m in metrics_list) / len(metrics_list))
                att_arr.append(sum(float(m['att']) for m in metrics_list) / len(metrics_list))
                art_arr.append(sum(float(m['art']) for m in metrics_list) / len(metrics_list))
        df = pd.DataFrame(
            {
                'avg_waiting_time': awt_arr,
                'avg_turnaround_time': att_arr,
                'avg_response_time': art_arr
            },
            index=['RR', 'priority_p', 'HRR', 'RR-SJF', 'WOA-DRR']
        )
        print(df)
        def bar_plot():
            df.plot.bar(rot=0)
            plt.title('scheduling algorithms chart')
            plt.xlabel('algorithms')
            plt.ylabel('time(second)')
            plt.grid()
            plt.show()
        button = ttk.Button(self, text="show chart", command=bar_plot)
        button.place(x=190, y=240)
        button1 = ttk.Button(self, text="Back", command=lambda: controller.show_frame(StartPage))
        button1.place(x=20, y=450)


class WOADRR(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.config(bg='#081547')
        label = ttk.Label(self, text="WOA-DRR (WOA-Optimized Dynamic Round Robin):", font=LARGE_FONT)
        label.grid(row=0, column=4, padx=10, pady=10)
        # Prepare tasks from data
        processes = [{"pid": row["process_id"], "burst_time": row["burst_time"]} for _, row in data.iterrows()]
        num_processors = 2
        quantum_min = 1
        quantum_max = 5
        population_size = 10
        max_iter = 30
        best_whale, best_fitness, progress = woa_optimize_assignment_quantum(
            processes, num_processors=num_processors, quantum_min=quantum_min, quantum_max=quantum_max,
            population_size=population_size, max_iter=max_iter, random_seed=42, verbose=False
        )
        assignment, quantums = best_whale
        # Show assignment and quantums
        label2 = ttk.Label(self, text=f"Best Quantums: {quantums}", font=LARGE_FONT, foreground='yellow')
        label2.place(x=20, y=150)
        # Show RR metrics for each processor
        processor_queues = [[] for _ in range(num_processors)]
        for i, proc in enumerate(assignment):
            processor_queues[proc].append(processes[i])
        y_offset = 200
        for idx, queue in enumerate(processor_queues):
            if queue:
                queue_df = pd.DataFrame({
                    'process_id': [t['pid'] for t in queue],
                    'burst_time': [t['burst_time'] for t in queue]
                })
                result = simulate_rr_algorithm(queue_df, quantums[idx], verbose=False, woa_label=True)
                label_proc = ttk.Label(self, text=f"Processor {idx+1} RR Metrics:", font=LARGE_FONT, foreground='yellow')
                label_proc.place(x=20, y=y_offset)
                label_throughput = ttk.Label(self, text=f"Throughput: {result['throughput']}", font=LARGE_FONT, foreground='yellow')
                label_throughput.place(x=20, y=y_offset+40)
                label_cpu = ttk.Label(self, text=f"CPU Utilization: {result['cpu_util']}", font=LARGE_FONT, foreground='yellow')
                label_cpu.place(x=20, y=y_offset+80)
                label_awt = ttk.Label(self, text=f"Avg Waiting Time: {result['awt']}", font=LARGE_FONT, foreground='yellow')
                label_awt.place(x=20, y=y_offset+120)
                label_att = ttk.Label(self, text=f"Avg Turnaround Time: {result['att']}", font=LARGE_FONT, foreground='yellow')
                label_att.place(x=20, y=y_offset+160)
                label_art = ttk.Label(self, text=f"Avg Response Time: {result['art']}", font=LARGE_FONT, foreground='yellow')
                label_art.place(x=20, y=y_offset+200)
                y_offset += 260
        button1 = ttk.Button(self, text="Back", command=lambda: controller.show_frame(StartPage))
        button1.place(x=20, y=y_offset)


class HRR(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.config(bg='#081547')
        label = ttk.Label(self, text="Hybrid Round Robin algorithm:", font=LARGE_FONT)
        label.grid(row=0, column=4, padx=10, pady=10)

        result = simulate_hrr_algorithm(data)
        set_data_for_chart(result)
        print_result(self, result)

        button1 = ttk.Button(self, text="Back", command=lambda: controller.show_frame(StartPage))
        button1.place(x=20, y=450)


class RRSJF(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.config(bg='#081547')
        label = ttk.Label(self, text="Round Robin SJF algorithm:", font=LARGE_FONT)
        label.grid(row=0, column=4, padx=10, pady=10)

        result = simulate_rrsjf_algorithm(data)
        set_data_for_chart(result)
        print_result(self, result)

        button1 = ttk.Button(self, text="Back", command=lambda: controller.show_frame(StartPage))
        button1.place(x=20, y=450)


if __name__ == "__main__":
    data = pd.read_csv("db/data_set.csv")
    LARGE_FONT = ("Arial", 25)

    awt_arr = []
    att_arr = []
    art_arr = []

    app = tkinterApp()
    app.wm_geometry("600x500")
    app.title('CPU Scheduling Algorithms Simulator')
    app.resizable(False, False)
    app.mainloop()