"""
Raspberry Pi Pico (MicroPython) exercise:
work with SIM7080G Cat-M/NBIoT Module
"""
from machine import Pin, ADC 
import os
import utime
import binascii

#print sys info
print(os.uname())

#using pin defined
ADC0= ADC(Pin(26))
sensor_temp = ADC(4)
led_pin =25  #onboard led
pwr_en = 14  #pin to control the power of the module
uart_port = 0
uart_baute = 115200

APN = "cmnbiot"

i=0
reading=0
temperature=0
rec_buff = ''

#uart setting
uart = machine.UART(uart_port, uart_baute, bits=8, parity=None, stop=1)

#LED indicator on Raspberry Pi Pico
led_onboard = machine.Pin(led_pin, machine.Pin.OUT)

# MQTT Server info
mqtt_host = '47.89.22.46'           
mqtt_port = '1883'

mqtt_topic1 = 'testtopic'
mqtt_topic2 = 'testtopic/led'
mqtt_topic3 = 'testtopic/temp'
mqtt_topic4 = 'testtopic/adc'
mqtt_topic5 = 'testtopic/tempwarning'
mqtt_topic6 = 'testtopic/warning'
mqtt_topic7 = 'testtopic/gpsinfo'

mqtt_msg = 'on'

def led_blink():
    led_onboard.value(1)
    utime.sleep(0.5)
    led_onboard.value(0)
    utime.sleep(0.5)
    led_onboard.value(1)
    utime.sleep(0.5)
    led_onboard.value(0)


#power on/off the module
def powerOn_Off(pwr_en):
    pwr_key = machine.Pin(pwr_en, machine.Pin.OUT)
    pwr_key.value(1)
    utime.sleep(2)
    pwr_key.value(0)

#Get ADC and temperature value of Raspberry Pi Pico
def ADC_temp():
    global reading
    global ADC0_reading
    global temperature
    ADC0_reading = ADC0.read_u16()*33/65535
    print("ADC0 voltage = {0:.2f}V \r\n".format(ADC0_reading))
    
    reading = sensor_temp.read_u16()*3.3/65535
    temperature = 27 - (reading - 0.706)/0.001721
    print("temperature = {0:.2f}℃ \r\n".format(temperature))
    
def hexStr_to_str(hex_str):
    hex = hex_str.encode('utf-8')
    str_bin = binascii.unhexlify(hex)
    return str_bin.decode('utf-8')

def str_to_hexStr(string):
    str_bin = string.encode('utf-8')
    return binascii.hexlify(str_bin).decode('utf-8')    
    
def waitResp_info(info='',timeout=2000):
    prvMills = utime.ticks_ms()
    info = b""
    while (utime.ticks_ms()-prvMills)<timeout:
        if uart.any():
            info = b"".join([info, uart.read(1)])
    print(info.decode())
    return info

#Send AT command
def sendAt(cmd,back,timeout=1000):
    rec_buff = b''
    uart.write((cmd+'\r\n').encode())
    prvMills = utime.ticks_ms()
    while (utime.ticks_ms()-prvMills)<timeout:
        if uart.any():
            rec_buff = b"".join([rec_buff, uart.read(1)])
    if rec_buff != '':
        if back not in rec_buff.decode():
            print(cmd + ' back:\t' + rec_buff.decode())
            return 0
        else:
            print(rec_buff.decode())
            return 1
    else:
        print(cmd + ' no responce')
            

#Module startup detection
def checkStart():
    while True:
        # simcom module uart may be fool,so it is better to send much times when it starts.
        uart.write( 'AT\r\n'.encode() )
        utime.sleep(2)
        uart.write( 'AT\r\n'.encode() )
        recBuff = waitResp_info()
        if 'OK' in recBuff.decode():
            print( 'SIM7080G is ready\r\n' + recBuff.decode() )
            recBuff = ''
            break 
        else:
            powerOn_Off(pwr_en)
            print( 'SIM7080G is starting up, please wait...\r\n')
            utime.sleep(5)

#Check the network status
def checkNetwork():
    sendAt("AT+CFUN=0","OK")
    sendAt("AT+CNMP=38","OK")      #Select LTE mode
    sendAt("AT+CMNB=2","OK")       #Select NB-IoT mode,if Cat-M，please set to 1
    sendAt("AT+CFUN=1","OK")
    utime.sleep(5)
    for i in range(1,10):
        if(sendAt("AT+CGREG?","0,1") == 1):
            print( 'SIM7080G is online\r\n')
            break
        else:
            print( 'SIM7080G is offline, please wait...\r\n')
            utime.sleep(5)
            continue
    sendAt("AT+CSQ","OK")
    sendAt("AT+CPSI?","OK")
    sendAt("AT+COPS?","OK")
    sendAt("AT+CGNAPN","OK")
    sendAt('AT+CNACT=0,1','OK')
    sendAt('AT+CNACT?','OK')
    
#Get the gps info
def getGpsInfo():
    count = 0 
    print('Start GPS session...')
    sendAt('AT+CGNSPWR=1','OK')
    utime.sleep(2)   
    for i in range(1,10):
        rec_buff = b''
        uart.write( 'AT+CGNSINF\r\n'.encode() )
        rec_buff = waitResp_info()
        if ',,,,' in rec_buff.decode():
            print('GPS is not ready：')
            print(rec_buff.decode())
            if i >= 9:
                print('GPS positioning failed, please check the GPS antenna!\r\n')
                sendAt('AT+CGNSPWR=0','OK')
            else:
                utime.sleep(2)
                continue
        else:
            if(count <= 3):
                count += 1
                print('GPS info:')
                print(rec_buff.decode())
            else:
                sendAt('AT+CGNSPWR=0','OK')
                break


#MQTT TEST
            #AT+CGDCONT=1,"IP","ctnb"
def mqttTest():
    sendAt('AT+SMCONF=\"URL\",'+mqtt_host+','+mqtt_port,'OK')
    sendAt('AT+SMCONF=\"KEEPTIME\",600','OK')
    sendAt('AT+SMCONF=\"CLIENTID\",\"Pico_SIM7080G\"','OK',2000)
    sendAt('AT+SMCONN','OK',5000)
    sendAt('AT+SMSUB=\"mqtt\",1','OK',5000)
    sendAt('AT+SMPUB=\"mqtt\",2,1,0','OK',2000)
    uart.write(mqtt_msg.encode())
    utime.sleep(2);
    sendAt('AT+SMUNSUB=\"mqtt\"','OK',2000)
    print('send message successfully!')
    sendAt('AT+SMDISC','OK',2000)
    
# HTTP GET TEST
def httpGetTest():
    sendCMD_waitResp("AT+CHTTPCREATE=\"http://api.seniverse.com\"")    #Create HTTP host instance
    sendCMD_waitResp("AT+CHTTPCON=0")           #Connect server
    sendCMD_waitRespLine("AT+CHTTPSEND=0,0,\"/v3/weather/now.json?key=SwwwfskBjB6fHVRon&location=shenzhen&language=en&unit=c\"")  #send HTTP request
    waitResp()
    sendCMD_waitResp("AT+CHTTPDISCON=0")      #Disconnected from server
    sendCMD_waitResp("AT+CHTTPDESTROY=0")      #Destroy HTTP instance

# HTTP POST TEST
def httpPostTest():
    global i
    i=i+1
    sendCMD_waitResp("AT+CHTTPCREATE=\"http://pico.wiki/post-data.php\"")    #Create HTTP host instance
    sendCMD_waitResp("AT+CHTTPCON=0")           #Connect server
    sendCMD_waitRespLine("AT+CHTTPSEND=0,1,\"/post-data.php\",4163636570743a202a2f2a0d0a436f6e6e656374696f6e3a204b6565702d416c6976650d0a557365722d4167656e743a2053494d434f4d5f4d4f44554c450d0a,\"application/x-www-form-urlencoded\","+str_to_hexStr("api_key=tPmAT5Ab3j888&value1="+str(temperature)+"&value2="+str(ADC0_reading)+"&value3="+str(i)))  #send HTTP request
    waitResp()
    sendCMD_waitResp("AT+CHTTPDISCON=0")      #Disconnected from server
    sendCMD_waitResp("AT+CHTTPDESTROY=0")      #Destroy HTTP instance

# SIM7080G main program
try:
    checkStart()
    checkNetwork()
    ADC_temp()
#    getGpsInfo()
    while True:
        utime.sleep(2)
        mqttTest()
    
except:
    print( 'Error!\r\n')
    powerOn_Off(pwr_en)
    




