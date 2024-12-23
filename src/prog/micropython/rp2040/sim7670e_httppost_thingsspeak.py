# import requests
#import pytz
# from datetime import datetime, timedelta
import json
import time


from machine import UART, Pin, SoftI2C

import utime

#Initialize the onboard LED as output
led = machine.Pin(25,machine.Pin.OUT)
# Toggle LED functionality
def BlinkLED(timer_one):
    led.toggle()
# import sdcard

# uart setting
uart_port = 0
uart_baute = 115200
Pico_SIM7670E = UART(uart_port, uart_baute)


HTTPINIT = "AT+HTTPINIT"
HTTPPARA = "AT+HTTPPARA=\"URL\",\""
HTTPACTION_GET = "AT+HTTPACTION=0"
HTTPACTION_POST = "AT+HTTPACTION=1"

HTTPHEAD = "AT+HTTPHEAD"

HTTPTERM = "AT+HTTPTERM"



# Send AT command
def send_at(cmd, back, timeout=1000):
    rec_buff = b''
    Pico_SIM7670E.write((cmd + '\r\n').encode())
    prvmills = utime.ticks_ms()
    while (utime.ticks_ms() - prvmills) < timeout:
        if Pico_SIM7670E.any():
            rec_buff = b"".join([rec_buff, Pico_SIM7670E.read(1)])
    if rec_buff != '':
        print(cmd + ' back:' + rec_buff.decode())
#         if back not in rec_buff.decode():
#             print(cmd + ' back:\t' + rec_buff.decode())
#             return 0
#         else:
#             print(rec_buff.decode())
#             return 1
    else:
        print(cmd + ' no responce')

def at_test():
    print("---------------------------SIM7080G AT TEST---------------------------")
    while True:
        try:
            command_input = str(input('Please input the AT command,press Ctrl+C to exit:\000'))
            send_at(command_input, 'OK', 2000)
        except KeyboardInterrupt:
            print('\n------Exit AT Command Test!------\r\n')
            module_power()
            print("------The module is power off!------\n")
            break

now = time.localtime()
timestr = "{}-{}-{} {}:{}:{} +0100".format(now[0], now[1], now[2],now[3], now[4],now[5])


if now[5] != 59:
    incr = now[5] + 1
else:
    incr = 0

timestr_1 = "{}-{}-{} {}:{}:{} +0100".format(now[0], now[1], now[2],now[3], now[4],incr)

# now = datetime.now(pytz.timezone('Europe/Zurich')).strftime('%Y-%m-%d %H:%M:%S %z')

url = 'http://api.thingspeak.com/channels/2755053/bulk_update.json'


myobj = json.dumps({
	"write_api_key": "S8MPZ4SE50EMGGA6",
	"updates": [{
			"created_at": timestr,
			"field1": "1.0",
			"field2": "2.0",
            "field3": "39.3"
		},
		{
			"created_at":  timestr_1,
			"field1": "100.1",
			"field2": "200.2",
            "field3": "399.2",
			"status": "hell yeah"
		}
	]
})

print(len(myobj))

# exit()

send_at("AT", "OK")
    
utime.sleep(1)

send_at("AT+CSQ", "OK")
    
utime.sleep(1)

send_at("AT+COPS?", "OK")

# Setups

send_at("AT+CNMP=2", "OK")

utime.sleep(1)

send_at("AT+CSCS=\"GSM\"", "OK")

utime.sleep(1)


send_at("AT+CNSMOD?", "OK")

utime.sleep(1)

send_at("AT+HTTPINIT", "OK")
    
#check and log values


post_para = HTTPPARA + url + "\"" # + f'sensor={sensor}&input={input_val}\"'


send_at(post_para, 'OK')

send_at("AT+HTTPPARA=\"CONTENT\",\"application/json\"", 'OK')


send_at("AT+HTTPDATA={},1000".format(len(myobj)),"OK")
send_at(myobj, "OK")

send_at(HTTPACTION_POST, 'OK')

send_at(HTTPHEAD, 'OK')

# # send_at("AT+HTTPTERM", "OK")
# timer_one = machine.Timer()
# # Timer one initialization for on board blinking LED at 200mS interval
# timer_one.init(freq=5, mode=machine.Timer.PERIODIC, callback=BlinkLED)

# print(type(myobj))
at_test()

#  
# x = requests.post(url, json = myobj)
# 
# print(x.reason)
# print(x.text)

