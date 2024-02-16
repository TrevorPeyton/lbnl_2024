import time
from machine import Pin
import sys
import uselect
from machine import RTC
import machine

spoll = uselect.poll()
spoll.register(sys.stdin, uselect.POLLIN)
rtc = RTC()

print("INIT")

SHIFT_REGISTER_SIZE = 16384
TDC_SHIFT_REGISTER_SIZE = 32

shift_out = False
shift_in = [0]
shift_out_counter = 0

shift_test = False
print_shift = False

tdc_test = True
tdc_shift = False
tdc_counter = 0

led_pin = Pin(25, Pin.OUT)
clock_pin = Pin(7, Pin.OUT)
reset_pin = Pin(8, Pin.OUT)  # reset is active low so invert all values
data_in_pin = Pin(9, Pin.OUT)
data_out_pins = [Pin(i, Pin.IN) for i in range(6)]

tdc_clk = Pin(17, Pin.OUT)  # clock
tdc_pulse_gen = Pin(11, Pin.OUT)  # high frequency pulse generator
tdc_and = Pin(12, Pin.IN)  # and flag for transient detected
tdc_rst = Pin(13, Pin.OUT)  # reset
tdc_in_swt = Pin(14, Pin.OUT)  # input switch
tdc_piso_sel = Pin(15, Pin.OUT)  # parallel in/serial out switch
tdc_hf_sel0 = Pin(27, Pin.OUT)  # high frequency select
tdc_hf_sel1 = Pin(28, Pin.OUT)  # high frequency select
tdc_res_sel0 = Pin(22, Pin.OUT)  # select 0 resolution
tdc_res_sel1 = Pin(26, Pin.OUT)  # select 1 resolution
tdc_out_pins = [Pin(i, Pin.IN) for i in [16, 19, 20, 21]]
tdc_target_test = Pin(10, Pin.OUT)  # target test

# tdc setup
reset_pin.value(1)
tdc_rst.value(0)
tdc_rst.value(1)
tdc_clk.value(0)
tdc_piso_sel.value(0)
tdc_res_sel0.value(1)
tdc_res_sel1.value(1)
tdc_in_swt.value(0)
tdc_hf_sel0.value(1)
tdc_hf_sel1.value(1)
tdc_target_test.value(0)


def date_time():
    # (year, month, mday, hour, minute, second, weekday, yearday)
    t = time.localtime()
    return f"{t[0]}-{t[1]}-{t[2]} {t[3]}-{t[4]}-{t[5]}-{t[6]}"


def log(msg, m="i"):
    print(f"{m}{date_time()} {msg}")


def reset_shift(delay=10):
    reset_pin.value(0)
    time.sleep_us(delay)
    reset_pin.value(1)
    time.sleep_us(delay)
    log("Shift Register Reset", "ls")


def reset_tdc(delay=2000):
    tdc_rst.value(0)
    time.sleep_us(delay)
    tdc_rst.value(1)
    time.sleep_us(delay)
    log("TDC Reset", "lt")


def set_led(v):
    led_pin.value(v)


def set_res(sel0, sel1):
    tdc_res_sel0.value(sel0)
    tdc_res_sel1.value(sel1)
    log(f"Resolution Set to {sel0}{sel1}", "lt")


def set_hf(sel0, sel1):
    tdc_hf_sel0.value(sel0)
    tdc_hf_sel1.value(sel1)
    log(f"High Frequency Gen Set to {sel0}{sel1}", "lt")


def set_tdc_in(sel):
    tdc_in_swt.value(sel)
    log(f"TDC Input Set to {sel}", "lt")
    time.sleep(1)


def hf_pulse(delay=100):
    reset_tdc()
    tdc_pulse_gen.value(0)
    time.sleep_us(delay)
    tdc_pulse_gen.value(1)
    time.sleep_us(delay)
    log(f"High Frequency Gen Pulsed", "lt")

    tdc_clk.value(1)
    tdc_piso_sel.value(1)


def target_pulse(delay=100):
    tdc_target_test.value(0)
    time.sleep_ms(1)
    tdc_target_test.value(1)
    time.sleep_ms(1)
    tdc_target_test.value(0)
    time.sleep_ms(1)
    log("Targets Pulsed", "lt")


def shift(v, delay=1):
    global data_out_pins
    led_pin.value(1)
    clock_pin.value(0)
    data_in_pin.value(v)
    o = [p.value() for p in data_out_pins]
    time.sleep_us(delay)
    clock_pin.value(1)
    led_pin.value(0)
    return o


def shift_tdc(delay=1):
    global tdc_out_pins
    tdc_clk.value(0)
    time.sleep_us(delay)
    tdc_clk.value(1)
    time.sleep_us(delay)
    return [p.value() for p in tdc_out_pins]


def blink(times, delay=1000):
    for _ in range(times):
        set_led(1)
        time.sleep_us(delay)
        set_led(0)
        time.sleep_us(delay)


def step():
    global shift_in
    global shift_out
    global shift_out_counter
    global tdc_test
    global tdc_shift
    global tdc_counter
    global c
    if shift_out:
        for v in shift_in:
            out_val = shift(v)
            shift_out_counter -= 1
            if print_shift:
                print(f"ds{''.join(str(x) for x in out_val)}")
            if shift_out_counter == 0:
                shift_out = False
                log("Finished Shifting Out", "ls")
                log("na", "fs")
                break
    if tdc_test or tdc_shift:
        # check for transient flag (AND flag)
        if tdc_and.value():
            if not tdc_shift:
                time.sleep_ms(1)  # delay in case and propagates before tdc is filled
                tdc_shift = True
                tdc_counter = TDC_SHIFT_REGISTER_SIZE
                tdc_piso_sel.value(0)  # parallel shift in
                tdc_clk.value(0)  # clock values in
                tdc_clk.value(1)
                tdc_piso_sel.value(1)  # set to serial shift out
                log("Transient Detected", "tt")

            # shift out values
            if tdc_shift:
                out_val = shift_tdc(0)
                print(f"dt{''.join(str(x) for x in out_val)}")
                tdc_counter -= 1
                if tdc_counter == 0:
                    tdc_shift = False
                    log("TDC Transient finished shifting out", "tf")
                    reset_tdc()

                    if not tdc_test:
                        log("na", "ft")


def configure_shift(
    new_shift_out_counter,
    new_shift_in,
    new_shift_out,
    new_shift_test,
    new_print_shift,
):
    global shift_out
    global shift_in
    global shift_out_counter
    global shift_test
    global print_shift
    shift_out = new_shift_out
    shift_in = new_shift_in
    shift_out_counter = new_shift_out_counter
    shift_test = new_shift_test
    print_shift = new_print_shift


blink(2, 1000000)
buffer = []
v = " "
while True:
    # non-blocking read until newline
    if spoll.poll(0):
        x = sys.stdin.read(1)
        if x == "\n":
            v = "".join(buffer)
            buffer = []
            blink(1, 10)
        else:
            buffer.append(x)

    step()

    if v[0] == "t":
        if (len(v) > 1) and (v[1] == "1"):
            tdc_test = True
            log("TDC Enabled", "lt")
            reset_tdc()
            time.sleep(1)
        else:
            tdc_test = False
            log("TDC Disabled", "lt")
            # sent finished if transient is not currently shifting out
            if not tdc_shift:
                log("na", "ft")
    if v[0] == "r":
        if len(v) == 3:
            set_res(int(v[1]), int(v[2]))
        else:
            log(f"Invalid Resolution Command {v} - Must be vXX where X is 0 or 1", "lt")
    if v[0] == "m":
        if len(v) == 2:
            if v[1] == "X":
                set_tdc_in(0)
                time.sleep(1)
                # test targets
                tdc_target_test.value(0)
                time.sleep_ms(1)
                tdc_target_test.value(1)
                time.sleep_ms(1)
                tdc_target_test.value(0)
                time.sleep_ms(1)
                log("Testing Targets", "lt")
            else:
                set_tdc_in(int(v[1]))
        else:
            log(
                f"Invalid TDC Input Selector Command {v} - Must be mX where X is 0 or 1",
                "lt",
            )
    if v[0] == "h":
        if len(v) == 3:
            set_hf(int(v[1]), int(v[2]))
        else:
            log(
                f"Invalid High Frequency Command {v} - Must be hXX where X is 0 or 1",
                "lt",
            )
    if v[0] == "p":
        hf_pulse()
    if v[0] == "o":
        target_pulse()
    if v[0] == "d":
        log("", m="d")
    if v[0] == "s":
        if len(v) <= 2 or v[1] not in ["h", "c", "s"]:
            log(
                "Invalid Shift Command - Must be sMX...X where M is 'h' or 'c' and X is 0 or 1",
                "e",
            )
        shift_in = [int(p) for p in v[2:]]
        if v[1] == "h":
            log(f"Starting Hold Shift Test with {shift_in} - Shifting bits in", "ls")
            configure_shift(
                new_shift_out_counter=SHIFT_REGISTER_SIZE,
                new_shift_in=shift_in,
                new_shift_out=True,
                new_shift_test=False,
                new_print_shift=False,
            )
        elif v[1] == "c":
            log(
                f"Starting Constant Shift Test with {shift_in} - Shifting bits in", "ls"
            )
            configure_shift(
                new_shift_out_counter=-1,
                new_shift_in=shift_in,
                new_shift_out=True,
                new_shift_test=True,
                new_print_shift=True,
            )
        elif v[1] == "s":
            log("Stopping Shift Test - Shifting bits out", "ls")
            configure_shift(
                new_shift_out_counter=SHIFT_REGISTER_SIZE,
                new_shift_in=[0, 1],
                new_shift_out=True,
                new_shift_test=False,
                new_print_shift=True,
            )
    v = " "
