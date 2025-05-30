import FreeSimpleGUI as sg
from constants import *
from layouts import *
import time
import pathlib
import numpy as np
import threading
import scipy as sp


class MainWindow:
    def __init__(
        self,
        run_log,
        devices,
        shift_window_generator,
        tdc_window_generator,
    ):
        self.run_log = run_log
        self.devices = devices
        self.tdc_enabled = False
        self.tdc_running = False
        self.shift_in = False
        self.shift_out = False
        self.shift_loaded = False
        self.shift_constant = False
        self.shifted_values = 0
        self.close_flag = False
        self.ps_status = False
        self.ps_toggle_lock = False
        self.ps_read_lock = False
        self.ps_file = None
        self.ps_a_latchup_counter = 0
        self.ps_a_latchup_counter = 0
        self.selected_rows = []
        self.last_values = {}
        self.current_config = {
            "TDC": None,
            "SHIFT": None,
        }
        self.create_path("data/ps_logs/")
        # create new file
        self.ps_file = open(f"data/ps_logs/ps.txt", "a")
        self.shift_window_generator = shift_window_generator
        self.tdc_window_generator = tdc_window_generator
        self.layout = [
            [LAYOUT_PS_CONFIG],
            [LAYOUT_TEST_CONFIG],
            [LAYOUT_SHIFT_CONFIG],
            [LAYOUT_HFPG_TDC_CONFIG],
            [LAYOUT_TABLE_MODIFICATIONS],
            LAYOUT_BOTTOM_CONTROLS,
            [LAYOUT_RUN_TABLE_CONFIG],
        ]
        self.main_window = sg.Window("LBNL 2024", self.layout, finalize=True, size=(1200,750))
        self.update_log(False)

        # start ps thread
        # self.ps_thread = threading.Thread(target=self.ps_threaded_loop)
        # self.ps_thread.start()

    def create_path(self, path):
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)

    def create_shift_file(self, run, f=None):
        if f is None:
            f = "shift"
        # make sure data/runs/{run} exists
        pathlib.Path(f"data/runs/{run}").mkdir(parents=True, exist_ok=True)
        # create a file for the shift data
        return open(f"data/runs/{run}/{f}.txt", "w")

    def create_log_file(self, run):
        # make sure data/runs/{run} exists
        pathlib.Path(f"data/runs/{run}").mkdir(parents=True, exist_ok=True)
        # create a file for the shift data
        return open(f"data/runs/{run}/log.txt", "w")

    def create_tdc_file(self, run):
        # make sure data/runs/{run} exists
        pathlib.Path(f"data/runs/{run}").mkdir(parents=True, exist_ok=True)
        # create a file for the shift data
        return open(f"data/runs/{run}/tdc.txt", "w")

    def save_log(self):
        # save as backup with time
        self.run_log.to_csv(
            f"data/runlogs/{time.strftime('%Y-%m-%d_%H-%M-%S')}.csv", index=False
        )
        self.run_log.to_csv("data/runlogs/latest.csv", index=False)

    def update_log(self, save=True):
        self.main_window["-RUN_LOG-"].update(self.run_log.values.tolist())
        if save:
            self.save_log()

    def compute_shift_transient(self, run):
        with open(f"data/runs/{run}/shift.txt", "r") as f:
            lines = f.readlines()
            lines = [l for l in lines if l != "\n"]
            data = np.stack([np.fromiter(line.strip(), dtype=np.int64) for line in lines]).T
        shift_data = self.current_config["SHIFT"]["shift_vals"]
        mask = np.array(shift_data * (data.shape[1] // len(shift_data)))[None].repeat(
            6, axis=0
        )
        # ignore last bit if it's not a full shift
        if mask.shape[1] < data.shape[1]:
            masked_data = np.logical_xor(data[:, :-1], mask)
        else:
            masked_data = np.logical_xor(data, mask)
        masked_data = np.logical_xor(data, mask)
        self.run_log.loc[self.run_log["run"] == run, "transients"] = masked_data.sum()
        self.update_log()

    def compute_tdc_transient(self, run):
        # count number of files in data/runs/{run} excluding log.txt
        count = 0
        for f in pathlib.Path(f"data/runs/{run}").iterdir():
            if f.is_file() and f.name != "log.txt":
                count += 1
        self.run_log.loc[self.run_log["run"] == run, "transients"] = count
        self.update_log()

    def pico_write(self, msg, flush=True):
        if DEBUG:
            return
        self.devices["pico"].write((msg + "\n").encode())
        if flush:
            self.devices["pico"].flush()

    def create_log(
        self, part, ion, let, angle, test_type, time, date, test_error=False
    ):
        # get the latest run number from run_log
        run = self.run_log["run"].max() + 1
        if run is None or np.isnan(run):
            run = 0

        # add a new row to run_log
        self.run_log.loc[len(self.run_log)] = [
            run,
            part,
            ion,
            let,
            angle,
            test_type,
            time,
            date,
            None,
            None,
            None,
            None,
            test_error,
        ]
        self.create_path(f"data/runs/{run}")
        return {"run": run}

    def pico_listen(self):
        if DEBUG:
            return
        if self.devices["pico"].in_waiting > 0:
            j = (
                self.devices["pico"]
                .read(self.devices["pico"].in_waiting)
                .decode("utf-8")
                .strip()
                .split("\n")
            )
            for i in j:
                if len(i) >= 2:
                    # data - shift registers
                    if i[:2] == "ds":
                        if self.current_config["SHIFT"]:
                            self.shifted_values += 1
                            try:
                                self.current_config["SHIFT"]["file"].write(i[2:] + "\n")
                            except Exception as e:
                                print(e)
                                import traceback

                                print(traceback.format_exc())
                            # update progress bar
                            # self.main_window["-PROG-"].update(
                            #     (self.shifted_values / SHIFT_REGISTER_SIZE) * 100
                            # )
                    # data - tdc
                    if i[:2] == "dt":
                        if self.current_config["TDC"]:
                            try:
                                self.shifted_values += 1
                                self.current_config["TDC"]["file"].write(i[2:] + "\n")
                            except Exception as e:
                                print(e)
                                import traceback

                                print(traceback.format_exc())
                    # log - shift registers
                    if i[:2] == "ls":
                        if self.current_config["SHIFT"]:
                            print(i[2:])
                            self.current_config["SHIFT"]["log_file"].write(i[2:] + "\n")
                    # transient triggered - tdc
                    if i[:2] == "tt":
                        if self.current_config["TDC"]:
                            print(i[2:])

                            # create a new file for the transient
                            self.current_config["TDC"]["file"] = self.create_shift_file(
                                self.current_config["TDC"]["run"],
                                self.current_config["TDC"]["transients"],
                            )
                            # increment the number of transients
                            self.current_config["TDC"]["transients"] += 1
                            self.current_config["TDC"]["log_file"].write(i[2:] + "\n")
                    # transient finished shifting out - tdc
                    if i[:2] == "tf":
                        if self.current_config["TDC"]:
                            print(i[2:])
                            self.current_config["TDC"]["log_file"].write(i[2:] + "\n")
                            if self.current_config["TDC"]["file"]:
                                self.current_config["TDC"]["file"].close()
                            self.current_config["TDC"]["file"] = None
                    # log - tdc
                    if i[:2] == "lt":
                        if self.current_config["TDC"]:
                            print(i[2:])
                            self.current_config["TDC"]["log_file"].write(i[2:] + "\n")
                    # finished - shift registers
                    if i[:2] == "fs":
                        if self.shift_in or self.shift_out:
                            # regardless we are not shifting anymore
                            self.shift_in = False
                            self.shift_out = False

                            # check if shift was just unloaded
                            if self.shift_loaded or self.shift_constant:
                                self.finalize_shift_test()
                            else:
                                # shift in finished
                                self.shift_loaded = True
                                self.main_window["-SHIFT-"].update(disabled=False)
                    # finished - tdc
                    if i[:2] == "ft":
                        self.tdc_running = False
                        self.main_window["-TDC-"].update("Start")
                        self.main_window["-TDC-"].update(disabled=False)
                        if self.current_config["TDC"]["file"]:
                            self.current_config["TDC"]["file"].close()
                        self.current_config["TDC"]["log_file"].close()
                        row = self.run_log["run"] == self.current_config["TDC"]["run"]
                        self.run_log.loc[
                            row,
                            "end_time",
                        ] = time.strftime("%H-%M-%S")
                        self.run_log.loc[
                            row,
                            "end_date",
                        ] = time.strftime("%Y-%m-%d")
                        self.compute_tdc_transient(self.current_config["TDC"]["run"])
                        self.update_log()

                        if self.last_values["-AUTO_OPEN-"]:
                            row_int = self.run_log[row].index[0]
                            # convert row (index) to int it is a boolean index
                            self.open_window(row_int)
                        self.current_config["TDC"] = None

    def stop_tdc(self):
        self.tdc_enabled = False
        self.main_window["-TDC-"].update(disabled=True)
        self.pico_write("t0")

    def start_tdc(self, values):
        self.tdc_running = True
        self.tdc_enabled = True
        self.main_window["-TDC-"].update("Stop")
        self.pico_write("t1")
        test_name = (
            f"set-{values['-HFRS-']}-{TDC_INPUT_MODES.index(values['-TDC_IS-'])}"
        )
        self.current_config["TDC"] = self.create_log(
            part=values["-PART-"],
            ion=values["-ION-"],
            let=values["-LET-"],
            angle=values["-ANGLE-"],
            test_type=test_name,
            time=time.strftime("%H-%M-%S"),
            date=time.strftime("%Y-%m-%d"),
            test_error=False if values["-TDC_IS-"] == "Targets" else True,
        )
        self.current_config["TDC"]["file"] = None
        self.current_config["TDC"]["log_file"] = self.create_log_file(
            self.current_config["TDC"]["run"]
        )
        self.current_config["TDC"]["transients"] = 0
        self.update_log()
        # get -TDC_IS- value and send to pico
        if values["-TDC_IS-"] == "Targets Test":
            self.pico_write("mX")
            self.stop_tdc()
        else:
            self.pico_write(f"m{0 if values['-TDC_IS-'] == 'Targets' else 1}")

    def finalize_shift_test(self):
        self.shift_loaded = False
        self.shift_constant = False

        # close file
        self.current_config["SHIFT"]["file"].close()
        self.current_config["SHIFT"]["log_file"].close()

        # get row as int
        row = self.run_log["run"] == self.current_config["SHIFT"]["run"]

        # update log with end time and date
        self.run_log.loc[
            row,
            "end_time",
        ] = time.strftime("%H-%M-%S")
        self.run_log.loc[
            row,
            "end_date",
        ] = time.strftime("%Y-%m-%d")

        self.compute_shift_transient(self.current_config["SHIFT"]["run"])
        self.update_log()

        self.current_config["SHIFT"] = None

        if self.last_values["-AUTO_OPEN-"]:
            row_int = self.run_log[row].index[0]
            # convert row (index) to int it is a boolean index
            self.open_window(row_int)

        # enable shift out button
        self.main_window["-SHIFT-"].update("Start")
        self.main_window["-SHIFT-"].update(disabled=False)

    def hard_stop_shift_test(self):
        self.main_window["-SHIFT-"].update("Start")
        self.main_window["-SHIFT-"].update(disabled=True)
        self.shift_in = False
        self.shift_out = False
        self.shifted_values = 0
        self.finalize_shift_test()

    def stop_shift_test(self):
        self.main_window["-SHIFT-"].update("Start")
        self.main_window["-SHIFT-"].update(disabled=True)
        self.shift_out = True
        self.pico_write("ss")
        self.shifted_values = 0

    def start_shift_test(self, values):
        self.main_window["-SHIFT-"].update("Stop")
        self.shift_in = True
        self.shift_loaded = False
        self.shift_type = "c" if values["-SHIFT_TYPE-"] == "Constant" else "h"
        self.current_config["SHIFT"] = self.create_log(
            part=values["-PART-"],
            ion=values["-ION-"],
            let=values["-LET-"],
            angle=values["-ANGLE-"],
            test_type=f"seu-{self.shift_type}-{values['-SHIFT_VAL-']}",
            time=time.strftime("%H-%M-%S"),
            date=time.strftime("%Y-%m-%d"),
            test_error=False,
        )
        self.current_config["SHIFT"]["file"] = self.create_shift_file(
            self.current_config["SHIFT"]["run"]
        )
        self.current_config["SHIFT"]["shift_vals"] = [
            int(i) for i in values["-SHIFT_VAL-"]
        ]
        self.current_config["SHIFT"]["log_file"] = self.create_log_file(
            self.current_config["SHIFT"]["run"]
        )
        self.update_log()

        if values["-SHIFT_TYPE-"] == "Hold":
            self.pico_write(f"sh{values['-SHIFT_VAL-']}")
            self.main_window["-SHIFT-"].update(disabled=True)
        elif values["-SHIFT_TYPE-"] == "Constant":
            self.shift_constant = True
            self.pico_write(f"sc{values['-SHIFT_VAL-']}")

    def open_window(self, row):
        test_type = self.run_log.iloc[row]["test_type"]
        if test_type.startswith("seu"):
            self.shift_window_generator(row)
        else:
            self.tdc_window_generator(row)

    def window_event_listen(self):
        event, values = self.main_window.read(timeout=1)
        self.last_values = values
        # exit event
        if event == sg.WIN_CLOSED or event == "Exit":
            return True

        if event == "-SHIFT-":
            if self.shift_loaded or self.shift_constant:
                self.stop_shift_test()
                # make sure progress bar is visible
                # self.main_window["-PROG-"].update(visible=True)
            if not self.shift_in and not self.shift_loaded:
                self.start_shift_test(values)
        if event == "-HFPS-":
            self.pico_write(f"h{values['-HFPS-']}")
        if event == "-HFRS-":
            self.pico_write(f"r{values['-HFRS-']}")
        if event == "-TDC-":
            if self.tdc_enabled:
                self.stop_tdc()
            else:
                self.start_tdc(values)
        if event == "-TDC_PULSE-":
            if self.tdc_enabled:
                self.pico_write("p")
        if event == "-RUN_LOG-":
            self.selected_rows = values["-RUN_LOG-"]
        if event == "-OPEN-":
            for row in self.selected_rows:
                # rows are inverted so invert row #
                self.open_window(row)
        if event == "-SANITY-":
            sg.popup_no_buttons(
                "",
                image=LAYOUT_SIDE_EYE,
                title="Warning",
                non_blocking=True,
                font=FONT,
            )
        if event == "-SET_FLUENCE-":
            # make sure values["-FLUX-"] is a valid number
            try:
                float(values["-FLUENCE-"])
            except ValueError:
                # non blocking popup
                sg.popup(
                    "Invalid fluence value", title="Error", non_blocking=True, font=FONT
                )
                return False
            if len(self.selected_rows) > 0:
                if len(self.selected_rows) > 1:
                    pass
                else:
                    # update flux on table
                    # self.run_log.loc[self.selected_rows[0], "flux"] = values["-FLUX-"]
                    self.run_log.loc[self.selected_rows[0], "fluence"] = values["-FLUENCE-"]
                    self.update_log()
        # if event == "-TOGGLE_PS-":
        #     if not self.ps_toggle_lock:
        #         self.ps_status = not self.ps_status
        #         if self.ps_status:
        #             self.main_window["-TOGGLE_PS-"].update(image_data=LAYOUT_BTN_ON)
        #         else:
        #             self.main_window["-TOGGLE_PS-"].update(image_data=LAYOUT_BTN_OFF)
        #         # create temp thread to toggle ps
        #         threading.Thread(
        #             target=self.ps_threaded_toggle, args=(self.ps_status,)
        #         ).start()
        # if event == "-UPDATE_PS-":
        #     self.main_window["-CH_A-"].update(values["-UPDATE_PS-"]["ch_a"])
        #     self.main_window["-CH_B-"].update(values["-UPDATE_PS-"]["ch_b"])

        if event == "-TDC_TARGET_PULSE-":
            print("pulse")
            self.pico_write("o")

        return False

    # def ps_threaded_toggle(self, on: bool, delay=0.5):
    #     if DEBUG:
    #         return
    #     self.ps_toggle_lock = True
    #     while self.ps_read_lock:
    #         continue
    #     if on:
    #         self.devices["ps"].write(f"INST {PS_CH1}")
    #         self.devices["ps"].write(f"VOLT 3.3")
    #         self.devices["ps"].write(f"OUTP ON")
    #         self.devices["ps"].write(f"INST {PS_CH2}")
    #         self.devices["ps"].write(f"VOLT 1.2")
    #         self.devices["ps"].write(f"OUTP ON")
    #     else:
    #         self.devices["ps"].write(f"INST {PS_CH1}")
    #         # self.devices["ps"].write(f"VOLT 0")
    #         self.devices["ps"].write(f"OUTP OFF")
    #         self.devices["ps"].write(f"INST {PS_CH2}")
    #         # self.devices["ps"].write(f"VOLT 0")
    #         self.devices["ps"].write(f"OUTP OFF")
    #     time.sleep(2)
    #     self.ps_toggle_lock = False

    # def latchup(self):
    #     self.ps_threaded_toggle(False, 0.05)
    #     self.ps_a_latchup_counter = 0
    #     self.ps_b_latchup_counter = 0
    #     if self.current_config["SHIFT"]:
    #         self.hard_stop_shift_test()
    #     self.ps_threaded_toggle(True, 0.05)
    #     # popup non blocking with button
    #     sg.popup_no_buttons(
    #         "",
    #         image=LAYOUT_SIDE_EYE,
    #         title="Warning",
    #         non_blocking=True,
    #         font=FONT,
    #     )
    #     time.sleep(2)

    # def ps_threaded_loop(self):
    #     if DEBUG:
    #         return
    #     while self.close_flag is False:
    #         try:
    #             # avoid writing/reading to ps which will trigger an error if we are enabling/disabling
    #             if self.ps_toggle_lock:
    #                 continue
    #             if self.close_flag or not self.main_window:
    #                 break

    #             self.ps_read_lock = True
    #             ch_a = float(self.devices["ps"].query(f"MEAS:CURR? {PS_CH1}"))
    #             ch_b = float(self.devices["ps"].query(f"MEAS:CURR? {PS_CH2}"))
    #             self.ps_read_lock = False

    #             if self.main_window is not None:
    #                 self.main_window.write_event_value(
    #                     "-UPDATE_PS-",
    #                     {
    #                         "ch_a": f"{ch_a:.3f}A",
    #                         "ch_b": f"{ch_b:.3f}A",
    #                     },
    #                 )
    #             if self.ps_file and self.ps_toggle_lock is False:
    #                 self.ps_file.write(
    #                     # date,time,psa,psb
    #                     f"{time.strftime('%Y-%m-%d,%H-%M-%S')},{ch_a},{ch_b}\n"
    #                 )
    #                 if ch_a > PS_THRESHOLD_A:
    #                     self.ps_a_latchup_counter += 1
    #                 else:
    #                     self.ps_a_latchup_counter = 0
    #                 if ch_b > PS_THRESHOLD_B:
    #                     self.ps_b_latchup_counter += 1
    #                 else:
    #                     self.ps_b_latchup_counter = 0

    #                 if self.ps_a_latchup_counter > PS_LATCH_CYCLES:
    #                     self.latchup()

    #                     self.ps_threaded_toggle(True, 0.05)
    #                 if self.ps_b_latchup_counter > PS_LATCH_CYCLES:
    #                     self.latchup()

    #         except Exception as e:
    #             print(e)
    #             # print full stack
    #             import traceback

    #             print(traceback.format_exc())
    #     if self.ps_file:
    #         self.ps_file.close()
    #     self.ps_threaded_toggle(False, 0.05)
    #     self.devices["ps"].close()

    def window_event_loop(self) -> bool:
        self.pico_listen()

        # will return True if window is closed
        return self.window_event_listen()

    def close(self):
        self.close_flag = True
        self.main_window.close()
        self.main_window = None
