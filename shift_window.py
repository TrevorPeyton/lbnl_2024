import PySimpleGUI as sg
from constants import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np


class ShiftWindow:
    def __init__(self, row, run_log):
        self.row = row
        self.run_log = run_log
        self.run: int = run_log.iloc[row]["run"]
        self.layout = [
            [
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
                    sg.Radio(
                        "All", group_id="REG", key="-REG-all-", font=FONT, default=True
                    ),
                    *[
                        sg.Radio(
                            f"{n}",
                            group_id="REG",
                            key=f"-REG-{n}-",
                            font=FONT,
                        )
                        for n in range(6)
                    ],
                ],
                [sg.Canvas(key="-CANVAS-", expand_x=True, expand_y=True)],
                [
                    sg.Multiline(
                        key="-LOG-",
                        disabled=True,
                        font=FONT,
                        expand_x=True,
                        expand_y=True,
                    )
                ],
                [sg.Button("Exit", font=FONT)],
            ]
        ]
        self.window: sg.Window = sg.Window(
            "Shift Test Results", self.layout, finalize=True, size=(1000, 800)
        )

        try:
            self.draw_figure(
                self.window["-CANVAS-"].TKCanvas, self.plot_shift_register(self.run, -1)
            )
        except Exception as e:
            print(e)

        # fill in the log
        with open(f"data/runs/{self.run}/log.txt", "r") as f:
            log = f.read()
            # put the log in the window
            self.window["-LOG-"].update(log)

    def get_run(self):
        return self.run

    def get_row(self):
        return self.row

    def bring_to_front(self):
        self.window.bring_to_front()

    def plot_shift_register(self, run, shift_register=-1):
        # -1 is all
        with open(f"data/runs/{run}/shift.txt", "r") as f:
            data = np.stack([np.fromiter(line.strip(), dtype=np.int64) for line in f])
        if data.shape[0] <= SHIFT_REGISTER_SIZE:
            data = np.pad(data, ((0, SHIFT_REGISTER_SIZE - data.shape[0]), (0, 0)))
        elif data.shape[0] > SHIFT_REGISTER_SIZE:
            data = data[:SHIFT_REGISTER_SIZE]
        data = data.T.reshape(6, -1, 128)
        fig, ax = plt.subplots(6, 1, figsize=(5, 2))
        if shift_register == -1:
            for p in range(6):
                ax[p].imshow(
                    data[p], aspect="auto", vmin=0, vmax=1, interpolation="none"
                )
                ax[p].set_yticks([])
                ax[p].set_xticks([])
                ax[p].set_ylabel(
                    f"SR{p}", rotation=0, position=(1.01, 0.5), ha="right", va="center"
                )

                for i in range(6):
                    # small font
                    ax[i].text(
                        138,
                        64,
                        f"{data[i].sum()}",
                        ha="right",
                        va="center",
                        fontsize=6,
                    )

            # fig.tight_layout()
            return fig
        else:
            data = data[shift_register]
            ax.set_title(f"Shift Register {shift_register}")
            ax.imshow(data, aspect="auto", vmin=0, vmax=1)
            ax.set_xticks([])
            fig.tight_layout()
            return fig

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

            try:
                if event.startswith("-REG-"):
                    if event.endswith("-all-"):
                        self.draw_figure(
                            self.window["-CANVAS-"].TKCanvas,
                            self.plot_shift_register(self.run, -1),
                        )
                    else:
                        self.draw_figure(
                            self.window["-CANVAS-"].TKCanvas,
                            self.plot_shift_register(
                                self.run, int(event.split("-")[-1])
                            ),
                        )
            except Exception as e:
                print(e)

        return False

    def close(self):
        self.window.close()
        self.window = None
