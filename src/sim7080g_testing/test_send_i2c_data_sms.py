import smbus
import time
import struct
import serial

from datetime import datetime

channel = 1

address = 0x19

outx_l = 0x28
outy_l = 0x06
outz_l = 0x08

bus = smbus.SMBus(channel)

bus.write_i2c_block_data(0x19,0x20, [0b01000111])

bus.write_i2c_block_data(0x19,0x23, [0b00001000])


ser = serial.Serial("/dev/serial0", 115200)
cmsg = "AT+CMGS=̣̣\"+41791384875\"\r\n"
msg = "test\x1a"
while True:
	time.sleep(1)
	accel_bytes = bus.read_i2c_block_data(0x19,0x28 | 0x80,6)
	accel_raw = struct.unpack('<hhh', bytearray(accel_bytes))
	print(accel_raw)
	print(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
	
ser.write("AT\r".encode())
msg=ser.read(64)
print(msg)

	
