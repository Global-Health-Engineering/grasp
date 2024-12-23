import machine
import os
import time
import utime
import gc

import sys

    

PORT= '/dev/serial0'

uart_port = 0
uart_baute = 115200
Pico_SIM7670E = machine.UART(uart_port, uart_baute)

cmgf = "AT+CMGF=1\r\n"
cscs = "AT+CSCS=\"GSM\"\r\n"
cmsg = 'AT+CMGS="+41791384875"\r'
msg = "test\x1a"


# # ~ ser.write(str.encode('AT\r\n'))
# ser.write(str.encode(cmgf))
# time.sleep(0.5)
# ser.write(str.encode(cscs))
# time.sleep(0.5)
# ser.write(str.encode(cmsg))
# time.sleep(0.5)
# ser.write(str.encode(msg))
# time.sleep(0.5)

#send at without \r\n
def send_at(cmd, back, timeout=7000):
    answer = True
    nothing_received = 100 #if nothing has been received for .1 seconds, it will exit the while loop and it will stay max 7 seconds in there
    rec_buff = b''
    Pico_SIM7670E.write((cmd + '\r\n').encode())
    prvmills = utime.ticks_ms()
    while (utime.ticks_ms() - prvmills) < timeout and (not answer or (utime.ticks_ms() - prvmills) < nothing_received):
        if Pico_SIM7670E.any():
            rec_buff = b"".join([rec_buff, Pico_SIM7670E.read(1)])
            answer = True
            prvmills = utime.ticks_ms()
        time.sleep(0.02)
    
    if rec_buff != b'':
        answer = rec_buff.decode()
        print(cmd + ' back:' + answer)
        if "OK" in answer or "DOWNLOAD" in answer or "202 Accepted" in answer:
            return True
        print ("ERROR found")
        return False
    else:
        print(cmd + ' no responce')
        return False
    
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


while True:  
    at_test()