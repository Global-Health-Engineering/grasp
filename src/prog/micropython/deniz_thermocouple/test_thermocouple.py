import time
from machine import Pin, SoftI2C
import adafruit_mcp9600

# frequency must be set for the MCP9600 to function.
# If you experience I/O errors, try changing the frequency.

    
i2c = SoftI2C(scl=Pin(5), sda=Pin(4), freq=100000)



print('I2C SCANNER')
devices = i2c.scan()

if len(devices) == 0:
  print("No i2c device !")
else:
  print('i2c devices found:', len(devices))

  for device in devices:
    print("I2C hexadecimal address: ", hex(device))
    
    
    
    
mcp = adafruit_mcp9600.MCP9600(i2c, address=102, tctype="K", tcfilter=0)
# 
# while True:
#     print((mcp.ambient_temperature, mcp.temperature, mcp.delta_temperature))
#     time.sleep(1)