import serial
import time

PORT= '/dev/serial0'

baud = 115200

ser = serial.Serial(PORT,baud,timeout = 1)

cmgf = "AT+CMGF=1\r\n"
cscs = "AT+CSCS=\"GSM\"\r\n"
cmsg = 'AT+CMGS="+41791384875"\r'
msg = "test\x1a"


# ~ ser.write(str.encode('AT\r\n'))
ser.write(str.encode(cmgf))
time.sleep(0.5)
ser.write(str.encode(cscs))
time.sleep(0.5)
ser.write(str.encode(cmsg))
time.sleep(0.5)
ser.write(str.encode(msg))
time.sleep(0.5)
while True:
	if ser.in_waiting > 0:
		line = ser.readline().decode().rstrip()
		print(line)
		time.sleep(0.1)

