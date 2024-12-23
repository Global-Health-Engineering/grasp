"""
Raspberry Pi Pico (MicroPython) exercise:
work with SIM7080G Cat-M/NBIoT Module
"""
import machine
import utime

# using pin defined
pwr_en = 14  # pin to control the power of the module

# uart setting
uart_port = 0
uart_baute = 115200
Pico_SIM7080G = machine.UART(uart_port, uart_baute)

# LED indicator on Raspberry Pi Pico
led_pin = 25  # onboard led
led_onboard = machine.Pin(led_pin, machine.Pin.OUT)

# HTTP Get Post Parameter
http_get_server = ['http://api.seniverse.com', '/v3/weather/now.json?key=SwwwfskBjB6fHVRon&location=shenzhen&language=en&unit=c']
http_post_server = ['http://pico.wiki', 'post-data.php', 'api_key=tPmAT5Ab3j888']
http_post_tmp = 'api_key=tPmAT5Ab3j888&value1=26.44&value2=57.16&value3=1002.95'


def led_blink():
    for i in range(1, 3):
        led_onboard.value(1)
        utime.sleep(1)
        led_onboard.value(0)
        utime.sleep(1)
    led_onboard.value(0)


# power on/off the module
def module_power():
    pwr_key = machine.Pin(pwr_en, machine.Pin.OUT)
    pwr_key.value(1)
    utime.sleep(2)
    pwr_key.value(0)


# Send AT command
def send_at(cmd, back, timeout=1500):
    rec_buff = b''
    Pico_SIM7080G.write((cmd + '\r\n').encode())
    prvmills = utime.ticks_ms()
    while (utime.ticks_ms() - prvmills) < timeout:
        if Pico_SIM7080G.any():
            rec_buff = b"".join([rec_buff, Pico_SIM7080G.read(1)])
    if rec_buff != '':
        if back not in rec_buff.decode():
            if 'ERROR' in rec_buff.decode():
                print(cmd + ' back:\t' + rec_buff.decode())
                return 0
            else:
                # Resend cmd
                rec_buff = b''
                rec_buff = send_at_wait_resp(cmd, back, timeout)
                if back not in rec_buff.decode():
                    print(cmd + ' back:\t' + rec_buff.decode())
                    return 0
                else:
                    return 1
        else:
            print(rec_buff.decode())
            return 1
    else:
        print(cmd + ' no responce\n')
        # Resend cmd
        rec_buff = send_at_wait_resp(cmd, back, timeout)
        if back not in rec_buff.decode():
            print(cmd + ' back:\t' + rec_buff.decode())
            return 0
        else:
            return 1


# Send AT command and return response information
def send_at_wait_resp(cmd, back, timeout=2000):
    rec_buff = b''
    Pico_SIM7080G.write((cmd + '\r\n').encode())
    prvmills = utime.ticks_ms()
    while (utime.ticks_ms() - prvmills) < timeout:
        if Pico_SIM7080G.any():
            rec_buff = b"".join([rec_buff, Pico_SIM7080G.read(1)])
    if rec_buff != '':
        if back not in rec_buff.decode():
            print(cmd + ' back:\t' + rec_buff.decode())
        else:
            print(rec_buff.decode())
    else:
        print(cmd + ' no responce')
    # print("Response information is: ", rec_buff)
    return rec_buff


# Module startup detection
def check_start():
    # simcom module uart may be fool,so it is better to send much times when it starts.
    send_at("AT", "OK")
    utime.sleep(1)
    for i in range(1, 4):
        if send_at("AT", "OK") == 1:
            print('------SIM7080G is ready------\r\n')
            send_at("ATE1", "OK")
            break
        else:
            module_power()
            print('------SIM7080G is starting up, please wait------\r\n')
            utime.sleep(5)


def set_network():
    print("Setting to NB-IoT mode:\n")
    send_at("AT+CFUN=0", "OK")
    send_at("AT+CNMP=38", "OK")  # Select LTE mode
    send_at("AT+CMNB=2", "OK")  # Select NB-IoT mode,if Cat-M，please set to 1
    send_at("AT+CFUN=1", "OK")
    utime.sleep(5)


# Check the network status
def check_network():
    if send_at("AT+CPIN?", "READY") != 1:
        print("------Please check whether the sim card has been inserted!------\n")
    for i in range(1, 10):
        if send_at("AT+CGATT?", "1"):
            print('------SIM7080G is online------\r\n')
            break
        else:
            print('------SIM7080G is offline, please wait...------\r\n')
            utime.sleep(5)
            continue
    send_at("AT+CSQ", "OK")
    send_at("AT+CPSI?", "OK")
    send_at("AT+COPS?", "OK")
    get_resp_info = str(send_at_wait_resp("AT+CGNAPN", "OK"))
    # getapn = get_resp_info.split('\"')
    # print(getapn[1])
    getapn1 = get_resp_info[get_resp_info.find('\"')+1:get_resp_info.rfind('\"')]
    # print(getapn1)
    send_at("AT+CNCFG=0,1,\""+getapn1+"\"", "OK")
    if send_at('AT+CNACT=0,1', 'ACTIVE'):
        print("Network activation is successful\n")
    else:
        print("Please check the network and try again!\n")
    send_at('AT+CNACT?', 'OK')


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


# Set HTTP body and head length
def set_http_length():
    send_at('AT+SHCONF=\"BODYLEN\",1024', 'OK')
    send_at('AT+SHCONF=\"HEADERLEN\",350', 'OK')


# Set HTTP header content
def set_http_content():
    send_at('AT+SHCHEAD', 'OK')
    send_at('AT+SHAHEAD=\"Content-Type\",\"application/x-www-form-urlencoded\"', 'OK')
    send_at('AT+SHAHEAD=\"User-Agent\",\"curl/7.47.0\"', 'OK')
    send_at('AT+SHAHEAD=\"Cache-control\",\"no-cache\"', 'OK')
    send_at('AT+SHAHEAD=\"Connection\",\"keep-alive\"', 'OK')
    send_at('AT+SHAHEAD=\"Accept\",\"*/*\"', 'OK')
    send_at('AT+SHCHEAD', 'OK')


# HTTP GET TEST
def http_get():
    send_at('AT+SHDISC', 'OK')
    send_at('AT+SHCONF="URL",\"'+http_get_server[0]+'\"', 'OK')
    set_http_length()
    send_at('AT+SHCONN', 'OK', 3000)
    if send_at('AT+SHSTATE?', '1'):
        set_http_content()
        resp = str(send_at_wait_resp('AT+SHREQ=\"'+http_get_server[1]+'\",1', 'OK',8000))
        # print("resp is :", resp)
        try:
            get_pack_len = int(resp[resp.rfind(',')+1:-5])
            if get_pack_len > 0:
                send_at_wait_resp('AT+SHREAD=0,'+str(get_pack_len), 'OK', 5000)
                send_at('AT+SHDISC', 'OK')
            else:
                print("HTTP Get failed!\n")
        except ValueError:
            print("ValueError!\n")
    else:
        print("HTTP connection disconnected, please check and try again\n")


# HTTP POST TEST
def http_post():
    send_at('AT+SHDISC', 'OK')
    send_at('AT+SHCONF="URL",\"' + http_post_server[0] + '\"', 'OK')
    set_http_length()
    send_at('AT+SHCONN', 'OK', 3000)
    if send_at('AT+SHSTATE?', '1'):
        set_http_content()
        send_at('AT+SHCPARA', 'OK')
        if send_at('AT+SHBOD=62,10000', '>', 1000) :
            send_at(http_post_tmp, 'OK')
            resp = str(send_at_wait_resp('AT+SHREQ=\"/'+http_post_server[1]+'\",3','OK', 8000))
            # print("resp is :", resp)
            try:
                get_pack = int(resp[resp.rfind(',')+1:-5])
                print(get_pack)
                if get_pack > 0:
                    send_at_wait_resp('AT+SHREAD=0,' + str(get_pack), 'OK', 3000)
                    send_at('AT+SHDISC', 'OK')
                else:
                    print("HTTP Post failed!\n")
            except ValueError:
                print("ValueError!\n")

        else:
            print("Send failed\n")

    else:
        print("HTTP connection disconnected, please check and try again\n")


# SIM7080G main program
led_blink()
check_start()
set_network()
check_network()
# while True:
print("http")
http_get()
http_post()

