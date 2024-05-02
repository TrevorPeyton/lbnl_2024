import PySimpleGUI as sg

import serial
import time
import glob
import os
import pathlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy as sp
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from constants import *
from main_window import MainWindow
from shift_window import ShiftWindow
from tdc_window import TDCWindow
import pyvisa

rm = pyvisa.ResourceManager()

sg.theme("Dark")


class App:
    def __init__(self):
        self.devices = {
            "pico": self.connect_to_pico(),
            "ps": None,
        }  # self.connect_to_ps()}
        self.create_log_paths()
        self.run_log = self.load_log()
        self.windows = [
            MainWindow(
                self.run_log,
                self.devices,
                self.create_shift_window,
                self.create_tdc_window,
            )
        ]

    def connect_to_pico(self):
        if DEBUG:
            return None
        pico = None
        path = None
        while True:
            try:
                l = glob.glob("/dev/tty.usbmodem*") + glob.glob("/dev/cu.usbmodem*")
                path = l[0]
                pico = serial.Serial(path, 115200)
            except:
                if len(l) == 0:
                    print("No Pico found")
                else:
                    print(f"Failed to connect to Pico at {path}")
                time.sleep(1)
                continue
            break
        return pico

    # def connect_to_ps(self):
    #     if DEBUG:
    #         return None
    #     while True:
    #         try:
    #             ps = rm.open_resource("TCPIP::192.168.4.5::INSTR")
    #             # ps = rm.open_resource("TCPIP::192.168.4.3::inst0::INSTR")
    #             return ps
    #         except Exception as e:
    #             print("Failed to connect to PS")
    #             time.sleep(1)

    def create_path(self, path):
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)

    def create_log_paths(self):
        self.create_path("data/runlogs")
        self.create_path("data/runs")

    def load_log(self):
        run_log = None
        if pathlib.Path("data/runlogs/latest.csv").exists():
            run_log = pd.read_csv("data/runlogs/latest.csv")
        else:
            run_log = pd.DataFrame(columns=LOG_COLUMNS)
            run_log.to_csv("data/runlogs/latest.csv", index=False)
        # set flux dtype to float64
        run_log["flux"] = run_log["flux"].astype("float64")
        return run_log

    def create_window(self, window_class, row, *args, **kwargs):
        for window in self.windows:
            if hasattr(window, "get_row") and (window.get_row() == row):
                window.bring_to_front()
                return
        new_window = window_class(row, *args, **kwargs)
        self.windows.append(new_window)

    def create_shift_window(self, row):
        self.create_window(ShiftWindow, row, self.run_log)

    def create_tdc_window(self, row):
        self.create_window(TDCWindow, row, self.run_log)

    def close_devices(self):
        if DEBUG:
            return
        if self.devices["pico"]:
            self.devices["pico"].close()


if __name__ == "__main__":
    app = App()
    while True:

        # window event loop
        for window in app.windows:
            if window.window_event_loop():
                window.close()
                app.windows.remove(window)
                break

        # if no windows, exit
        if len(app.windows) == 0:
            break

    # close devices
    app.close_devices()
