import smbus
import time
import struct
import serial
import random
from datetime import datetime

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(filename='log_SIM7670G.log', format='%(asctime)s %(message)s',encoding='utf-8', level=logging.DEBUG)


link_suff = "https://script.google.com/macros/s/AKfycbx_0crLR8ErDBV_EST0TE1bXNz_dIPdIaI0_DwJjJbLWbSuPDrreUR5NieqyBke2zBD/exec?"
# "sensor=[35]&input=[04052024]"


PORT= '/dev/serial0'

baud = 115200

ser = serial.Serial(PORT,baud,timeout = 1)

cmgf = "AT+CMGF=1\r\n"
cscs = "AT+CSCS=\"GSM\"\r\n"
cmsg = 'AT+CMGS="+41791384875"\r'
esc = "\x1a"


HTTPINIT = "AT+HTTPINIT"
HTTPPARA = "AT+HTTPPARA=\"URL\",\""
HTTPACTION = "AT+HTTPACTION=0"

HTTPHEAD = "AT+HTTPHEAD"

HTTPTERM = "AT+HTTPTERM"

# "200 OK" in str
# AT+HTTPHEAD
# +HTTPHEAD: 226
# HTTP/1.1 200 OK
# Date: Tue, 12 Nov 2024 10:24:17 GMT
# Content-Type: application/json
# Content-Length: 254
# Connection: keep-alive
# Server: gunicorn/19.9.0
# Access-Control-Allow-Origin: *
# Access-Control-Allow-Credentials: true

def logprint(msg, mode=0):
    if mode == 0:
        print(msg)
        logger.info(msg)
    elif mode = 1:
        print(msg)
    else mode = 2:
        logger.info(msg)



# Send AT command and return response information
# def send_at_wait_resp(cmd, back, timeout=2):
#     rec_buff = b''
#     Pico_SIM7080G.write((cmd + '\r\n').encode())
#     prvmills = utime.ticks_ms()
#     while (utime.ticks_ms() - prvmills) < timeout:
#         if Pico_SIM7080G.any():
#             rec_buff = b"".join([rec_buff, Pico_SIM7080G.read(1)])
#     if rec_buff != '':
#         if back not in rec_buff.decode():
#             print(cmd + ' back:\t' + rec_buff.decode())
#         else:
#             print(rec_buff.decode())
#     else:
#         print(cmd + ' no responce')
#     print("Response information is: ", rec_buff)
#     return rec_buff

# COMMANDS:
# - AT+CSCS=GSM
# - AT+CPIN?
# - AT+CSQ
# - AT+CNMP=
# - AT+CREG?
# - AT+COPS?
# - AT+HTTPTERM

def read_lines():
    resp=ser.readlines()
    if len(resp):
        for i in resp:
            logprint(i.decode())
        return resp   
    else:
        logprint('None read_line (no response)')
        return None

def sent_at(cmd, back, timeout=2):
    logprint(str.encode(cmd + "\r\n"))
    ser.write(str.encode(cmd + "\r\n"))
    
    time.sleep(timeout)
    
    resp = read_lines()
    if resp != None:
        for i in resp:
            if back in i:
                return "back in response"
            else:
                return "back not in response"
    else:
        return "no response"
    
def setup():
    
    # Checks:
    while send_at("AT", "OK") != "back in response":
        logprint('Connection or module not working')
        time.sleep(2)
        
    time.sleep(1)
    
    while send_at("AT+CPIN?", "READY") != "back in response":
        logprint('No sim response')
        time.sleep(2)
        
    time.sleep(1)
    
    send_at("AT+CSQ", "OK")
    
    time.sleep(1)
    
    send_at("AT+COPS?", "OK")
    
    # Setups
    
    send_at("AT+CNMP=2", "OK")
    
    time.sleep(1)
    
    send_at("AT+CSCS=\"GSM\"", "OK")
    
    time.sleep(1)

    
    send_at("AT+CBSMOD?", "OK")
    
    time.sleep(1)


while True:
    
    #check and log values
    
    send_at("AT+CSQ", "OK")
    
    time.sleep(1)
    
    send_at("AT+COPS?", "OK")
    
    time.sleep(1)

    
    send_at("AT+CBSMOD?", "OK")
    
    time.sleep(1)
    
    
    # make httprequest
    
    input_val = str(round(random.random(),3))
    sensor = str(datetime.now().strftime("%d_%m_%Y_%H_%M_%S"))
    request_command = HTTPPARA + link_suff + f'sensor={sensor}&input={input_val}\"'
    
    send_at(request_command, 'OK')
    
    send_at(HTTPACTION, 'OK')
    
    send_at(HTTPHEAD, 'OK')
    
