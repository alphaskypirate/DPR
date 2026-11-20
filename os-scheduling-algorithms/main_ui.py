"""CPU Scheduling Simulator - GUI.

Thesis: Enhancing Round Robin with Whale Optimization Algorithm.
Run from anywhere:  python main_ui.py
"""
import os
import queue
import statistics
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import matplotlib
import pandas as pd

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for folder in ("Round-Robin-scheduling", "WOA-Dynamic-Round-Robin-scheduling"):
    sys.path.append(os.path.join(BASE_DIR, folder))
sys.path.append(BASE_DIR)

from RR import simulate_rr_algorithm
from Hybrid_RR import simulate_hrr_algorithm
from RRSJF import simulate_rrsjf_algorithm
from woa_drr import run_woa_drr

DEFAULT_CSV = os.path.join(BASE_DIR, "db", "data_set.csv")
REQUIRED_COLUMNS = {"process_id", "arrival_time", "burst_time"}

# ---- look & feel -------------------------------------------------------------------------
BG = "#0b1437"
PANEL = "#111c44"
CARD = "#1b2559"
ACCENT = "#4f8cff"
HIGHLIGHT = "#ff9f43"
TEXT = "#ffffff"
MUTED = "#9aa7d1"
FONT = "Segoe UI"


# ---- algorithm registry ------------------------------------------------------------------
def _woa_info(result):
    q = result["quantums"]
    text = (f"Quantums chosen by WOA: min {min(q)}, median {int(statistics.median(q))}, max {max(q)}  "
            f"(plain RR uses one fixed value for every process)")
    if result.get("order") is not None:
        text += "\nReady-queue order was also optimized."
    return text


class Algo:
    def __init__(self, key, label, short, description, runner, params=(), info=None):
        self.key, self.label, self.short = key, label, short
        self.description, self.runner, self.params, self.info = description, runner, params, info


ALGOS = [
    Algo("rr", "Round Robin", "RR",
         "Each process gets a fixed time quantum in turn. Honours arrival times.",
         lambda d, p: simulate_rr_algorithm(d, p["quantum"], verbose=False),
         params=[dict(name="quantum", label="Time quantum", type="int", default=1, low=1, high=1000)]),
    Algo("hrr", "Hybrid Round Robin", "HRR",
         "Per cycle the quantum is the smallest remaining burst among arrived processes, "
         "which are served shortest first.",
         lambda d, p: simulate_hrr_algorithm(d, verbose=False)),
    Algo("rrsjf", "Round Robin + SJF", "RR-SJF",
         "Per cycle the quantum is the average remaining burst of arrived processes, "
         "served shortest first.",
         lambda d, p: simulate_rrsjf_algorithm(d)),
    Algo("woa", "WOA-DRR (proposed)", "WOA-DRR",
         "Whale Optimization Algorithm searches a time quantum for every process (and "
         "optionally the processor assignment and ready-queue order). Fitness = average "
         "waiting time + weight x average response time. Takes about 20-60 seconds.",
         lambda d, p: run_woa_drr(d, num_processors=p["processors"], response_weight=p["weight"],
                                  optimize_order=p["order"], use_arrival=p["arrival"]),
         params=[dict(name="processors", label="Processors", type="int", default=1, low=1, high=4),
                 dict(name="weight", label="Response-time weight", type="float", default=0.5),
                 dict(name="order", label="Also optimize ready-queue order", type="bool", default=False),
                 dict(name="arrival", label="Use arrival times", type="bool", default=True)],
         info=_woa_info),
]
ALGO_BY_KEY = {a.key: a for a in ALGOS}

METRICS = [("n", "Processes", ""), ("awt", "Avg waiting time", "seconds"),
           ("att", "Avg turnaround time", "seconds"), ("art", "Avg response time", "seconds")]


# ---- application -------------------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CPU Scheduling Algorithms Simulator - Enhancing Round Robin with WOA")
        self.geometry("1200x800")
        self.minsize(1100, 780)
        self.configure(bg=BG)

        self.data = None
        self.csv_path = DEFAULT_CSV
        self.results = {}
        self.busy = False
        self.events = queue.Queue()
        self.pages = {}
        self.nav_buttons = {}

        self._init_style()
        self._build_layout()
        self.load_csv(DEFAULT_CSV, quiet=True)
        self.show_page("dataset")
        self.after(100, self._poll)

    # -- styling
    def _init_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=BG, foreground=TEXT, font=(FONT, 11))
        s.configure("TFrame", background=BG)
        s.configure("Panel.TFrame", background=PANEL)
        s.configure("Card.TFrame", background=CARD)
        s.configure("TLabel", background=BG, foreground=TEXT)
        s.configure("Panel.TLabel", background=PANEL)
        s.configure("Muted.TLabel", foreground=MUTED)
        s.configure("Title.TLabel", font=(FONT, 22, "bold"))
        s.configure("Sub.TLabel", foreground=MUTED, font=(FONT, 11))
        s.configure("CardValue.TLabel", background=CARD, font=(FONT, 22, "bold"), foreground=TEXT)
        s.configure("CardName.TLabel", background=CARD, font=(FONT, 10), foreground=MUTED)
        s.configure("TButton", background=ACCENT, foreground=TEXT, font=(FONT, 11, "bold"),
                    padding=(14, 8), borderwidth=0)
        s.map("TButton", background=[("active", "#6ea0ff"), ("disabled", "#34406e")],
              foreground=[("disabled", MUTED)])
        s.configure("Nav.TButton", background=PANEL, foreground=MUTED, anchor="w", padding=(18, 10),
                    font=(FONT, 11))
        s.map("Nav.TButton", background=[("active", CARD)], foreground=[("active", TEXT)])
        s.configure("NavActive.TButton", background=CARD, foreground=TEXT, anchor="w", padding=(18, 10),
                    font=(FONT, 11, "bold"))
        s.map("NavActive.TButton", background=[("active", CARD)])
        s.configure("TCheckbutton", background=BG, foreground=TEXT, font=(FONT, 11))
        s.map("TCheckbutton", background=[("active", BG)])
        s.configure("TEntry", fieldbackground=CARD, foreground=TEXT, insertcolor=TEXT)
        s.configure("TSpinbox", fieldbackground=CARD, foreground=TEXT, arrowcolor=TEXT, background=CARD)
        s.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT, rowheight=26,
                    borderwidth=0, font=(FONT, 10))
        s.configure("Treeview.Heading", background=CARD, foreground=TEXT, font=(FONT, 10, "bold"),
                    relief="flat")
        s.map("Treeview", background=[("selected", ACCENT)])
        s.configure("Vertical.TScrollbar", background=CARD, troughcolor=PANEL, arrowcolor=TEXT,
                    bordercolor=PANEL, lightcolor=CARD, darkcolor=CARD)
        s.map("Vertical.TScrollbar", background=[("active", ACCENT)])
        s.configure("Horizontal.TProgressbar", background=ACCENT, troughcolor=CARD, borderwidth=0)

    # -- layout
    def _build_layout(self):
        sidebar = ttk.Frame(self, style="Panel.TFrame", width=250)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        ttk.Label(sidebar, text="CPU Scheduling\nSimulator", style="Panel.TLabel",
                  font=(FONT, 17, "bold"), justify="left").pack(anchor="w", padx=18, pady=(22, 2))
        ttk.Label(sidebar, text="Enhancing Round Robin\nwith Whale Optimization", style="Panel.TLabel",
                  foreground=MUTED, font=(FONT, 10), justify="left").pack(anchor="w", padx=18, pady=(0, 16))

        self._add_nav(sidebar, "dataset", "Dataset")
        ttk.Label(sidebar, text="ALGORITHMS", style="Panel.TLabel", foreground=MUTED,
                  font=(FONT, 9, "bold")).pack(anchor="w", padx=18, pady=(14, 2))
        for algo in ALGOS:
            self._add_nav(sidebar, algo.key, algo.short if algo.key != "woa" else "WOA-DRR  (proposed)")
        ttk.Label(sidebar, text="RESULTS", style="Panel.TLabel", foreground=MUTED,
                  font=(FONT, 9, "bold")).pack(anchor="w", padx=18, pady=(14, 2))
        self._add_nav(sidebar, "compare", "Compare all")

        self.content = ttk.Frame(self)
        self.content.pack(side="left", fill="both", expand=True)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.pages["dataset"] = DatasetPage(self.content, self)
        for algo in ALGOS:
            self.pages[algo.key] = AlgoPage(self.content, self, algo)
        self.pages["compare"] = ComparePage(self.content, self)
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

    def _add_nav(self, parent, key, text):
        b = ttk.Button(parent, text=text, style="Nav.TButton", command=lambda: self.show_page(key))
        b.pack(fill="x")
        self.nav_buttons[key] = b

    def show_page(self, key):
        for k, b in self.nav_buttons.items():
            b.configure(style="NavActive.TButton" if k == key else "Nav.TButton")
        self.pages[key].tkraise()
        if hasattr(self.pages[key], "refresh"):
            self.pages[key].refresh()

    # -- data
    def load_csv(self, path, quiet=False):
        try:
            df = pd.read_csv(path)
            missing = REQUIRED_COLUMNS - set(df.columns)
            if missing:
                raise ValueError(f"missing column(s): {', '.join(sorted(missing))}")
        except Exception as exc:
            if not quiet:
                messagebox.showerror("Could not load dataset", str(exc))
            return
        self.data = df
        self.csv_path = path
        self.results.clear()
        for page in self.pages.values():
            if hasattr(page, "on_data_changed"):
                page.on_data_changed()

    # -- running algorithms in a worker thread (the GUI never freezes)
    def run_jobs(self, keys):
        if self.busy:
            return
        if self.data is None:
            messagebox.showwarning("No dataset", "Load a dataset first.")
            return
        try:
            # WOA-DRR settings live on its own page, so read them for every run
            jobs = [(k, self.pages[k].collect_params() if hasattr(self.pages[k], "collect_params") else {})
                    for k in keys]
        except ValueError as exc:
            messagebox.showerror("Invalid parameter", str(exc))
            return
        self.busy = True
        for page in self.pages.values():
            if hasattr(page, "set_busy"):
                page.set_busy(True)
        data = self.data.copy()

        def work():
            for key, params in jobs:
                self.events.put(("start", key))
                try:
                    result = ALGO_BY_KEY[key].runner(data.copy(), params)
                    self.events.put(("result", key, result))
                except Exception as exc:  # show the error instead of silently killing the thread
                    self.events.put(("error", key, f"{type(exc).__name__}: {exc}"))
            self.events.put(("done",))

        threading.Thread(target=work, daemon=True).start()

    def _poll(self):
        try:
            while True:
                ev = self.events.get_nowait()
                kind = ev[0]
                if kind == "result":
                    self.results[ev[1]] = ev[2]
                if kind == "done":
                    self.busy = False
                handler = {"start": "on_start", "result": "on_result", "error": "on_error",
                           "done": None}[kind]
                for page in self.pages.values():
                    if kind == "done":
                        if hasattr(page, "set_busy"):
                            page.set_busy(False)
                    elif hasattr(page, handler):
                        getattr(page, handler)(*ev[1:])
        except queue.Empty:
            pass
        self.after(100, self._poll)


class Header(ttk.Frame):
    def __init__(self, parent, title, subtitle):
        super().__init__(parent)
        ttk.Label(self, text=title, style="Title.TLabel").pack(anchor="w")
        ttk.Label(self, text=subtitle, style="Sub.TLabel", wraplength=820, justify="left").pack(anchor="w", pady=(4, 0))


# ---- pages -------------------------------------------------------------------------------
class DatasetPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.configure(padding=28)
        Header(self, "Dataset", "Processes the algorithms are simulated on. "
                                "Use a CSV with process_id, arrival_time, burst_time.").pack(anchor="w")

        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=16)
        ttk.Button(bar, text="Load CSV...", command=self.choose).pack(side="left")
        self.run_btn = ttk.Button(bar, text="Run all algorithms", command=self.run_all)
        self.run_btn.pack(side="left", padx=10)
        self.summary = ttk.Label(self, text="", style="Muted.TLabel")
        self.summary.pack(anchor="w", pady=(0, 8))

        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True)
        cols = ("process_id", "arrival_time", "burst_time")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c.replace("_", " ").title())
            self.tree.column(c, anchor="center", width=140)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def choose(self):
        path = filedialog.askopenfilename(title="Choose dataset", filetypes=[("CSV files", "*.csv")],
                                          initialdir=os.path.join(BASE_DIR, "db"))
        if path:
            self.app.load_csv(path)

    def run_all(self):
        self.app.show_page("compare")
        self.app.run_jobs([a.key for a in ALGOS])

    def set_busy(self, busy):
        self.run_btn.configure(state="disabled" if busy else "normal")

    def on_data_changed(self):
        d = self.app.data
        self.tree.delete(*self.tree.get_children())
        for row in d[["process_id", "arrival_time", "burst_time"]].itertuples(index=False):
            self.tree.insert("", "end", values=tuple(row))
        self.summary.configure(
            text=f"{os.path.basename(self.app.csv_path)}  |  {len(d)} processes  |  "
                 f"arrival {d.arrival_time.min()} - {d.arrival_time.max()}  |  "
                 f"burst {d.burst_time.min()} - {d.burst_time.max()} (mean {d.burst_time.mean():.0f})")


class AlgoPage(ttk.Frame):
    def __init__(self, parent, app, algo):
        super().__init__(parent)
        self.app, self.algo = app, algo
        self.vars = {}
        self.configure(padding=28)
        Header(self, algo.label, algo.description).pack(anchor="w")

        if algo.params:
            box = ttk.Frame(self)
            box.pack(anchor="w", pady=(18, 0))
            for p in algo.params:
                row = ttk.Frame(box)
                row.pack(anchor="w", pady=3)
                if p["type"] == "bool":
                    var = tk.BooleanVar(value=p["default"])
                    ttk.Checkbutton(row, text=p["label"], variable=var).pack(side="left")
                else:
                    var = tk.StringVar(value=str(p["default"]))
                    ttk.Label(row, text=p["label"], width=22).pack(side="left")
                    if p["type"] == "int":
                        ttk.Spinbox(row, from_=p["low"], to=p["high"], textvariable=var, width=8).pack(side="left")
                    else:
                        ttk.Entry(row, textvariable=var, width=10).pack(side="left")
                self.vars[p["name"]] = var

        bar = ttk.Frame(self)
        bar.pack(anchor="w", pady=18, fill="x")
        self.run_btn = ttk.Button(bar, text="Run simulation", command=lambda: app.run_jobs([algo.key]))
        self.run_btn.pack(side="left")
        self.status = ttk.Label(bar, text="", style="Muted.TLabel")
        self.status.pack(side="left", padx=14)
        self.progress = ttk.Progressbar(bar, mode="indeterminate", length=220)

        grid = ttk.Frame(self)
        grid.pack(fill="x", pady=(4, 0))
        self.value_labels = {}
        for i, (key, name, unit) in enumerate(METRICS):
            card = ttk.Frame(grid, style="Card.TFrame", padding=(18, 14))
            card.grid(row=i // 2, column=i % 2, sticky="nsew", padx=(0, 14), pady=(0, 14))
            grid.grid_columnconfigure(i % 2, weight=1)
            val = ttk.Label(card, text="-", style="CardValue.TLabel")
            val.pack(anchor="w")
            ttk.Label(card, text=name + (f"  ({unit})" if unit else ""), style="CardName.TLabel").pack(anchor="w")
            self.value_labels[key] = val
        self.info = ttk.Label(self, text="", style="Muted.TLabel", wraplength=820, justify="left")
        self.info.pack(anchor="w", pady=(6, 0))

    def collect_params(self):
        out = {}
        for p in self.algo.params:
            raw = self.vars[p["name"]].get()
            try:
                if p["type"] == "bool":
                    out[p["name"]] = bool(raw)
                elif p["type"] == "int":
                    v = int(raw)
                    if not p["low"] <= v <= p["high"]:
                        raise ValueError
                    out[p["name"]] = v
                else:
                    v = float(raw)
                    if v < 0:
                        raise ValueError
                    out[p["name"]] = v
            except ValueError:
                raise ValueError(f"'{p['label']}' has an invalid value: {raw}")
        return out

    def _stop_progress(self):
        self.progress.stop()
        self.progress.pack_forget()

    def on_data_changed(self):
        for lbl in self.value_labels.values():
            lbl.configure(text="-")
        self.info.configure(text="")
        self.status.configure(text="")

    def set_busy(self, busy):
        self.run_btn.configure(state="disabled" if busy else "normal")

    def on_start(self, key):
        if key == self.algo.key:
            self.status.configure(text="Running...")
            self.progress.pack(side="left")
            self.progress.start(12)

    def on_result(self, key, result):
        if key != self.algo.key:
            return
        for k, lbl in self.value_labels.items():
            lbl.configure(text=str(result[k]).strip())
        self.status.configure(text="Done")
        self.info.configure(text=self.algo.info(result) if self.algo.info else "")
        self._stop_progress()

    def on_error(self, key, message):
        if key == self.algo.key:
            self.status.configure(text="Failed")
            self._stop_progress()
            messagebox.showerror(f"{self.algo.label} failed", message)


class ComparePage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.configure(padding=28)
        Header(self, "Compare all algorithms",
               "Runs every algorithm on the current dataset. Times use the CPU time unit measured on this "
               "machine, so compare values within one run.").pack(anchor="w")

        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=14)
        self.run_btn = ttk.Button(bar, text="Run all algorithms",
                                  command=lambda: app.run_jobs([a.key for a in ALGOS]))
        self.run_btn.pack(side="left")
        self.status = ttk.Label(bar, text="WOA-DRR uses the settings on its own page.", style="Muted.TLabel")
        self.status.pack(side="left", padx=14)

        cols = ("algo", "awt", "att", "art")
        heads = ("Algorithm", "Avg waiting (s)", "Avg turnaround (s)", "Avg response (s)")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=len(ALGOS))
        for c, h in zip(cols, heads):
            self.tree.heading(c, text=h)
            self.tree.column(c, anchor="center" if c != "algo" else "w", width=190 if c != "algo" else 260)
        self.tree.tag_configure("woa", foreground=HIGHLIGHT)
        self.tree.pack(fill="x")

        self.fig = Figure(figsize=(9, 2.8), dpi=100, facecolor=BG)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().configure(bg=BG, highlightthickness=0, width=10, height=10)  # size comes from the layout
        self.canvas.get_tk_widget().pack(fill="both", expand=True, pady=(14, 0))
        self.draw()

    def refresh(self):
        self.draw()

    def on_data_changed(self):
        self.status.configure(text="Dataset changed - run the algorithms again.")
        self.refresh_table()
        self.draw()

    def set_busy(self, busy):
        self.run_btn.configure(state="disabled" if busy else "normal")
        if not busy:
            self.status.configure(text="Done. WOA-DRR uses the settings on its own page.")

    def on_start(self, key):
        self.status.configure(text=f"Running {ALGO_BY_KEY[key].short}...")

    def on_result(self, key, result):
        self.refresh_table()
        self.draw()

    def on_error(self, key, message):
        self.status.configure(text=f"{ALGO_BY_KEY[key].short} failed: {message}")

    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for algo in ALGOS:
            r = self.app.results.get(algo.key)
            if r:
                self.tree.insert("", "end", tags=("woa",) if algo.key == "woa" else (),
                                 values=(algo.label, r["awt"].strip(),
                                         r["att"].strip(), r["art"].strip()))

    def draw(self):
        self.fig.clear()
        done = [a for a in ALGOS if a.key in self.app.results]
        if not done:
            self.fig.text(0.5, 0.5, "Run the algorithms to see the comparison chart", color=MUTED,
                          ha="center", va="center", fontsize=12)
            self.canvas.draw_idle()
            return
        names = [a.short for a in done]
        colors = [HIGHLIGHT if a.key == "woa" else ACCENT for a in done]
        for i, (key, title) in enumerate((("awt", "Avg waiting time (s)"), ("att", "Avg turnaround time (s)"),
                                          ("art", "Avg response time (s)"))):
            ax = self.fig.add_subplot(1, 3, i + 1)
            ax.bar(names, [float(self.app.results[a.key][key]) for a in done], color=colors)
            ax.set_title(title, color=TEXT, fontsize=10)
            ax.set_facecolor(PANEL)
            ax.tick_params(colors=MUTED, labelsize=7)
            for label in ax.get_xticklabels():
                label.set_rotation(55)
                label.set_ha("right")
            for spine in ax.spines.values():
                spine.set_color(CARD)
            ax.grid(axis="y", color=CARD, linewidth=0.6)
            ax.set_axisbelow(True)
        self.fig.tight_layout()
        self.canvas.draw_idle()


if __name__ == "__main__":
    App().mainloop()
