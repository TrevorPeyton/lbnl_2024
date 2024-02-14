import machine
import time
import uctypes

# Define shift register input, reset, and clock pin numbers
shift_register_input_pin_num = 9
shift_register_reset_pin_num = 8
shift_register_clock_pin_num = 7
DFRTP1_3_register_out_pin_num = 4
DFXTP1_1_register_out_pin_num = 3

# Initialize GPIO pins
shift_register_input_pin = machine.Pin(shift_register_input_pin_num, machine.Pin.OUT)
shift_register_reset_pin = machine.Pin(shift_register_reset_pin_num, machine.Pin.OUT)
shift_register_clock_pin = machine.Pin(shift_register_clock_pin_num, machine.Pin.OUT)
outs = [machine.Pin(i, machine.Pin.IN) for i in range(6)]

delay = 1
first = 0
second = 1

for n in range(10):
    shift_register_reset_pin.value(0)
    time.sleep_ms(1)
    shift_register_reset_pin.value(1)
    time.sleep_ms(1)
    # Set the reset pin and input pin to 3.3V (high)
    # DFRTP1_3_Out = []
    # DFXTP1_1_Out = []
    counts = [0 for _ in range(6)]
    for i in range(8192):
        shift_register_clock_pin.value(0)
        shift_register_input_pin.value(0)
        time.sleep_us(delay)
        shift_register_clock_pin.value(1)
        time.sleep_us(delay)
        shift_register_clock_pin.value(0)
        shift_register_input_pin.value(1)
        time.sleep_us(delay)
        shift_register_clock_pin.value(1)
        time.sleep_us(delay)
        # if i % 10 == 0:
        #     print(i)
    for i in range(8192):
        shift_register_clock_pin.value(0)
        shift_register_input_pin.value(0)
        time.sleep_us(delay)
        shift_register_clock_pin.value(1)
        time.sleep_us(delay)
        for j in range(6):
            if outs[j].value() == 1:
                counts[j] += 1
        shift_register_clock_pin.value(0)
        shift_register_input_pin.value(1)
        time.sleep_us(delay)
        shift_register_clock_pin.value(1)
        time.sleep_us(delay)
        for j in range(6):
            if outs[j].value() == 1:
                counts[j] += 1
        # if i % 100 == 0:
        #     print(i)
    # count_ones = 0
    # count_zeros = 0
    # count_ones2 = 0
    # count_zeros2 = 0
    # # Loop through the array
    # for element in DFRTP1_3_Out:
    #     if element == 1:
    #         count_ones += 1
    #     elif element == 0:
    #         count_zeros += 1
    # for element in DFXTP1_1_Out:
    #     if element == 1:
    #         count_ones2 += 1
    #     elif element == 0:
    #         count_zeros2 += 1
    # Print the results
    print(counts)
