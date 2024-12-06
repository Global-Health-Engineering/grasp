# I2C Scanner MicroPython
from machine import Pin, SoftI2C
import time
import gc 

# You can choose any other combination of I2C pins
i2c = SoftI2C(scl=Pin(5), sda=Pin(4))

print('I2C SCANNER')
devices = i2c.scan()

if len(devices) == 0:
  print("No i2c device !")
else:
  print('i2c devices found:', len(devices))

  for device in devices:
    print("I2C hexadecimal address: ", hex(device))
    
    
    
# The MIT License (MIT)
#
# Copyright (c) 2016 Philip R. Moyer and Radomir Dopieralski for Adafruit Industries.
#
""" PCF8523 Real Time Clock (RTC) module for MicroPython

Jun. 2020 Meurisse D. for MCHobby (shop.mchobby.be) - backport to MicroPython
Nov. 2016 Philip R. Moyer and Radomir Dopieralski for Adafruit Industries - original version for CircuitPython

- Milliseconds are not supported by this RTC.
- Datasheet: http://cache.nxp.com/documents/data_sheet/PCF8523.pdf
- based on https://github.com/adafruit/Adafruit_CircuitPython_PCF8523.git
"""


STANDARD_BATTERY_SWITCHOVER_AND_DETECTION = 0b000
BATTERY_SWITCHOVER_OFF = 0b111

RTC_REG = 0x03
ALARM_REG = 0x0A
CONTROL_1_REG = 0x00

def _bcd2bin(value):
	"""Convert binary coded decimal to Binary """
	return value - 6 * (value >> 4)


def _bin2bcd(value):
	"""Convert a binary value to binary coded decimal."""
	return value + 6 * (value // 10)

class PCF8523:
	"""Interface to the PCF8523 RTC."""

	def __init__(self, i2c ):
		self.i2c = i2c
		self.address = 0x68
		self.buf1 = bytearray(1)
		self.buf7 = bytearray(7)

		# Try and verify this is the RTC we expect by checking the timer B
		# frequency control bits which are 1 on reset and shouldn't ever be
		# changed.
		self.retries = 2
		while self.retries > 0:
			self.buf1[0] = 0x12
			self.i2c.writeto( self.address, self.buf1 )
			self.i2c.readfrom_into( self.address, self.buf1 )
			if (self.buf1[0] & 0b00000111) != 0b00000111 and self.retries == 2:				
				self.soft_reset()
			elif (self.buf1[0] & 0b00000111) != 0b00000111 and self.retries == 1:
				raise ValueError("Unable to find PCF8523 at i2c address 0x68.")
			self.retries -= 1

	def soft_reset(self):
		self.buf1 = bytearray(1)
		self.buf1[0] = 0x58
		self.i2c.writeto_mem(self.address, CONTROL_1_REG, self.buf1) # writes 0x58 to address 0x00 to reset the chip

	def _read_datetime( self, time_reg ):
		"""Gets the date and time from a given register location (0x03 for RTC, 0x0A for alarm )."""
		weekday_offset = 1
		weekday_start  = 0

		self.buf1[0] = time_reg
		self.i2c.writeto( self.address, self.buf1 )
		self.i2c.readfrom_into( self.address, self.buf7 )
		#CircuitPython struct_time (tm_year=1999, tm_mon=12, tm_mday=31, tm_hour=17, tm_min=4, tm_sec=58, tm_wday=4, tm_yday=365, tm_isdst=0)
		#MicroPython mktime (year, month, mday, hour, minute, second, weekday, yearday)
		return time.mktime((
				_bcd2bin(self.buf7[6]) + 2000,
				_bcd2bin(self.buf7[5]),
				_bcd2bin(self.buf7[4 - weekday_offset]),
				_bcd2bin(self.buf7[2]),
				_bcd2bin(self.buf7[1]),
				_bcd2bin(self.buf7[0] & 0x7F),
				_bcd2bin(self.buf7[3 + weekday_offset] - weekday_start),
				-1,
				-1,  ))

	def _write_datetime( self, time_reg, value ):
		""" set the time from the tuple (year, month, mday, hour, minute, second, weekday, yearday) on the given register (0x03 for RTC, 0x0A for alarm)"""
		weekday_offset = 1
		weekday_start  = 0

		self.buf7[0] = _bin2bcd(value[5]) & 0x7F  # tm_sec format conversions
		self.buf7[1] = _bin2bcd(value[4]) # tm_min
		self.buf7[2] = _bin2bcd(value[3]) # tm_hour
		self.buf7[3 + weekday_offset] = _bin2bcd(
		    value[6] + weekday_start # tm_wday
		)
		self.buf7[4 - weekday_offset] = _bin2bcd(value[2]) # tm_mday
		self.buf7[5] = _bin2bcd(value[1]) # tm_mon
		self.buf7[6] = _bin2bcd(value[0] - 2000) # tm_year

		self.i2c.writeto_mem( self.address, time_reg, self.buf7 )

	@property
	def datetime(self):
		"""Gets or Set the current date and time then starts the clock."""
		return self._read_datetime( RTC_REG )

	@datetime.setter
	def datetime(self, value ):
		""" set the current time from the tuple (year, month, mday, hour, minute, second, weekday, yearday) """
		# Automatically sets lost_power to false.
# 		self.power_management = STANDARD_BATTERY_SWITCHOVER_AND_DETECTION

		self._write_datetime( RTC_REG, value )
# 
# i2c = I2C(0)

rtc = PCF8523( i2c )

# Year: 2020, month: 6, day: 22, hour: 0, min: 14, sec: 6, weekday: 0 (monday), yearday: 174
# yearday can be set to 0 when setting the date... it will be recomputed
rtc.datetime = (2020, 6, 22, 0, 14, 6, 0, 174)
time.sleep(1)

while(1):
    print(gc.mem_free())
    print(gc.mem_alloc())
#     gc.collect()


    # Reread time from RTC
    _time = rtc.datetime
    print( "Time: %s secs" % _time )
    print( "Year: %s, month: %s, day: %s, hour: %s, min: %s, sec: %s, weekday: %s, yearday: %s" % time.localtime(_time) )

    days = ['monday','tuesday', 'wednesday', 'thursday', 'friday', 'saterday', 'sunday' ]
    weekday = time.localtime(_time)[6]
    print( 'Day of week: %s' % days[weekday] )
    time.sleep(0.1)
