import serial
import time

path = "/dev/cu.usbmodem2101"

s = serial.Serial(path, 115200)

s.write(b"0\n")
out = []
time.sleep(2)
s.write(b"c\n")
time.sleep(2)
out.append(s.read(s.inWaiting()).decode("ascii"))

# dump out to file
with open("out.txt", "w") as f:
    f.write("".join(out))
