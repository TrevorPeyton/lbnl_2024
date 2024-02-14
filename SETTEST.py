import machine
import time
import uctypes

# Define shift register input, reset, and clock pin numbers
SET_CLK_pin_num = 17
HFPULSEIN_pin_num = 11
AND_FLAG_pin_num = 12
RST_pin_num = 13
TDCINSWTCH_pin_num = 14
PISO_SEL_pin_num = 15
HFS1_pin_num = 28
HFS0_pin_num = 27
S1_pin_num = 26
S0_pin_num = 22

# Initialize GPIO pins
SET_CLK_input_pin = machine.Pin(SET_CLK_pin_num, machine.Pin.OUT)
HFPULSEIN_pin = machine.Pin(HFPULSEIN_pin_num, machine.Pin.OUT)
AND_FLAG_pin = machine.Pin(AND_FLAG_pin_num, machine.Pin.IN)
RST_pin = machine.Pin(RST_pin_num, machine.Pin.OUT)
TDCINSWTCH_pin = machine.Pin(TDCINSWTCH_pin_num, machine.Pin.OUT)
PISO_SEL_pin = machine.Pin(PISO_SEL_pin_num, machine.Pin.OUT)
HFS1_pin = machine.Pin(HFS1_pin_num, machine.Pin.OUT)
HFS0_pin = machine.Pin(HFS0_pin_num, machine.Pin.OUT)
S1_pin = machine.Pin(S1_pin_num, machine.Pin.OUT)
S0_pin = machine.Pin(S0_pin_num, machine.Pin.OUT)
outs = [machine.Pin(i, machine.Pin.IN) for i in [16, 19, 20, 21]]
a = machine.Pin(10, machine.Pin.OUT)

# Reset
time.sleep_ms(4)
RST_pin.value(0)
time.sleep(4)
RST_pin.value(1)
time.sleep_ms(4)
# Configure Circuit

SET_CLK_input_pin.value(0)
PISO_SEL_pin.value(0)
S1_pin.value(1)
S0_pin.value(1)
TDCINSWTCH_pin.value(0)
time.sleep_ms(1)

# PRERAD TEST
HFS0_pin.value(1)
HFS1_pin.value(1)
a.value(0)
a.value(1)
a.value(0)


# Test
HFPULSEIN_pin.value(0)

HFPULSEIN_pin.value(1)

andout = AND_FLAG_pin.value()

SET_CLK_input_pin.value(1)

PISO_SEL_pin.value(1)

out = [0 for _ in range(len(outs))]
for i in range(32):
    SET_CLK_input_pin.value(0)

    SET_CLK_input_pin.value(1)

    for j in range(len(outs)):
        if outs[j].value() == 1:
            out[j] += 1
# print(i)
print(out)
# print([32 - o for o in out])
# count_ones = 0
# count_zeros = 0
# for x in Out:
#     if x == 1:
#         count_ones += 1
#     elif x == 0:
#         count_zeros += 1
# print(count_ones)
print("Value of AND_FLAG_pin:", andout)
