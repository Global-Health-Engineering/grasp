
import smbus
import time
import struct
import serial
import random

from datetime import datetime

channel = 1

address = 0x19

outx_l = 0x28
outy_l = 0x06
outz_l = 0x08

bus = smbus.SMBus(channel)

bus.write_i2c_block_data(0x19,0x20, [0b01000111])

bus.write_i2c_block_data(0x19,0x23, [0b00001000])


PORT= '/dev/serial0'

baud = 115200

ser = serial.Serial(PORT,baud,timeout = 1)

cmgf = "AT+CMGF=1\r\n"
cscs = "AT+CSCS=\"GSM\"\r\n"
cmsg = 'AT+CMGS="+41791384875"\r'
esc = "\x1a"

previous_accel_raw = "";

def readprintlines():
	time.sleep(0.5)
	resp=ser.readlines()
	for i in resp:
		print(i.decode())
		
def getsensordata():
	accel_bytes = bus.read_i2c_block_data(0x19,0x28 | 0x80,6)
	accel_raw = struct.unpack('<hhh', bytearray(accel_bytes))
	return accel_raw
	
while True:
	# Sleeping time: 5min + random * 2min
	
	accel_raw = getsensordata()
	
	ser.write(str.encode(cmgf))
	readprintlines()

	ser.write(str.encode(cscs))
	readprintlines()
	
	ser.write(str.encode(cmsg))
	readprintlines()
	
	ser.write(str.encode(datetime.now().strftime("%d/%m/%Y %H:%M:%S") +"\nPrevious:"+str(previous_accel_raw) + "\nCurrent:"+str(accel_raw) + esc))
	time.sleep(2)
	

	readprintlines()
	previous_accel_raw = accel_raw
	time.sleep(5*60 + random.random()*2*60)

	
