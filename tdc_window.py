import PySimpleGUI as sg
from constants import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import pathlib


class TDCWindow:
    def __init__(self, row, run_log):
        self.row = row
        self.run_log = run_log
        self.run = run_log.iloc[row]["run"]
        self.tdc_fig = None
        self.files = [
            int(f.name[:-4])
            for f in pathlib.Path(f"data/runs/{self.run}").iterdir()
            if f.is_file() and f.suffix == ".txt" and not f.name == "log.txt"
        ]
        self.files.sort()
        first_file = self.files[0] if len(self.files) > 0 else None
        self.layout = [
            [
                sg.Table(
                    [self.run_log.iloc[row].values.tolist()],
                    headings=LOG_COLUMNS,
                    auto_size_columns=True,
                    justification="center",
                    num_rows=1,
                    key="-SHIFT-INFO-",
                    font=FONT,
                    expand_x=True,
                ),
            ],
            [
                sg.TabGroup(
                    [
                        [
                            sg.Tab(
                                "Overview",
                                [
                                    [sg.Canvas(key="-CANVAS_0-")],
                                ],
                                font=FONT,
                            ),
                            sg.Tab(
                                "Individual TDCs",
                                layout=[
                                    [sg.Canvas(key="-CANVAS_1-")],
                                    [
                                        sg.Frame(
                                            "TDC Selection",
                                            layout=[
                                                [
                                                    sg.Listbox(
                                                        self.files,
                                                        size=(20, 4),
                                                        key="-TDC_SEL-",
                                                        expand_x=True,
                                                        font=FONT,
                                                        enable_events=True,
                                                        default_values=[first_file],
                                                    )
                                                ],
                                            ],
                                            expand_x=True,
                                        ),
                                    ],
                                ],
                                font=FONT,
                                expand_x=True,
                            ),
                        ],
                    ],
                    expand_x=True,
                    font=FONT,
                )
            ],
            [
                sg.Multiline(
                    size=(50, 5),
                    key="-LOG-",
                    disabled=True,
                    font=FONT,
                    expand_x=True,
                )
            ],
            [sg.Button("Exit", font=FONT)],
        ]
        self.window = sg.Window(
            "Shift Test Results",
            self.layout,
            finalize=True,
        )

        self.draw_figure(self.window["-CANVAS_0-"].TKCanvas, self.plot_tdc_summary())

        self.tdc_agg = self.draw_figure(
            self.window["-CANVAS_1-"].TKCanvas, self.plot_single_tdc(first_file)
        )

        with open(f"data/runs/{self.run}/log.txt", "r") as f:
            log = f.read()
            self.window["-LOG-"].update(log)

    def get_run(self):
        return self.run

    def get_row(self):
        return self.row

    def bring_to_front(self):
        self.window.bring_to_front()

    def get_data(self):
        data_list = []
        for f in pathlib.Path(f"data/runs/{self.run}").iterdir():
            if f.is_file() and f.suffix == ".txt" and not f.name == "log.txt":
                data_list.append([])
                with open(f, "r") as file:
                    for line in file:
                        data_list[-1].append(np.fromiter(line.strip(), dtype=np.int64))
        return np.stack(data_list) if len(data_list) > 0 else None

    def plot_tdc_summary(self):
        stacked_data = self.get_data()
        if stacked_data is not None:
            fig, ax = plt.subplots(1, 1, figsize=(3, 2))
            fig.suptitle(f"Run {self.run} TDC Transient Summary")
            ax.boxplot(stacked_data.sum(axis=1), labels=[f"{i}" for i in range(4)])
            ax.set_xlabel("TDC")
            ax.set_ylabel("Transients")
            fig.tight_layout()
            return fig
        return None

    def plot_single_tdc(self, transient):
        stacked_data = self.get_data()
        if stacked_data is not None:
            if self.tdc_fig:
                self.tdc_im.set_data(stacked_data[transient, :].T)
                self.tdc_fig.suptitle(f"Transient {transient} TDC")
                self.tdc_agg.draw()
            else:
                self.tdc_fig, self.tdc_ax = plt.subplots(1, 1, figsize=(4, 2))
                self.tdc_im = self.tdc_ax.imshow(
                    stacked_data[transient, :].T, vmin=0, vmax=1, interpolation="none"
                )
                self.tdc_fig.suptitle(f"Transient {transient} TDC")
                self.tdc_ax.set_ylabel("TDC")
                self.tdc_ax.set_yticks(np.arange(0, 4))
                self.tdc_ax.set_xlabel("Bit")
                self.tdc_ax.invert_yaxis()
                self.tdc_fig.tight_layout()
            return self.tdc_fig
        return None

    def draw_figure(self, canvas, figure):
        figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
        figure_canvas_agg.draw()
        figure_canvas_agg.get_tk_widget().pack(side="top", fill="both", expand=1)
        return figure_canvas_agg

    def window_event_loop(self):
        if self.window:
            event, values = self.window.read(timeout=1)
            if event == sg.WIN_CLOSED or event == "Exit":
                return True
            if event == "-TDC_SEL-":
                self.plot_single_tdc(values["-TDC_SEL-"][0])
        return False

    def close(self):
        self.window.close()
