import machine
import os
import time
import utime
import gc
import adafruit_mcp9600

######### MAIN OPERATIONAL VARIABLES ###########
numb = "+41791384875"

uploadperiod = 10#20*60

temp_thr = 60
uploadperiod_thr = 5*60


#enable garbage collector
gc.enable()

#turn on and off debugging, use: debug_print() for debugging
DEBUG = True

#blinking when uploading
blink = True




if blink:
    led = machine.Pin(25, machine.Pin.OUT)


# #Variables
# APIkey = "QUP42CU3RK1X6R2Z"                                                           #*****************               Update personal APIkey                    **************************
# Channel = "2716690"                                                                   #*****************                  Update Channel ID                      **************************
# updateperiod = 5                                                                      #*****************        Update how often your sensors take samples       **************************
# amount_samples = 10                                                                   #*****************     After how many samples do you want to save it to the SD card    **************************
                                                                    #*****************   Update how often the data is uploaded to thinkspeak (lowest that is useful is 20sec)   **************************
# max_entries = 200


#*********Start RTC Setup (time not relevant)***********
system_rtc = machine.RTC()
system_rtc.datetime((2020, 1, 21, 2, 10, 32, 36, 0))

last_upload_day = None
update_counter = 0
collected_data = []
upload_state = 0  # Global state variable
last_upload_time = utime.time()  # Tracks the time of the last step
last_update_time = utime.time()
last_update_time_holder = utime.time()
upload_step_time = utime.time()


#*********Start Thermocouple Setup***********
i2c = machine.I2C(id = 0, scl=machine.Pin(5), sda=machine.Pin(4), freq=1000)
# rtc = urtc.PCF8523(i2c)
mcp = adafruit_mcp9600.MCP9600(i2c, address=102, tctype="K", tcfilter=0)

#*********Operational variables***********
sleeping = False
upload_success = True

#*********SIM_7670E setup***********
uart_port = 0
uart_baute = 115200
Pico_SIM7670E = machine.UART(uart_port, uart_baute)

# #HTTP commands
# HTTPINIT = "AT+HTTPINIT\r\n"
# HTTPPARA = "AT+HTTPPARA=\"URL\",\"\r\n"
# HTTPACTION_GET = "AT+HTTPACTION=0\r\n"
# HTTPACTION_POST = "AT+HTTPACTION=1\r\n"
# HTTPHEAD = "AT+HTTPHEAD\r\n"
# HTTPTERM = "AT+HTTPTERM\r\n"
# 
# #sleepmode commands
# Read_Command = "AT+CSCLK?\r\n"
# Test_Command = "AT+CSCLK=?\r\n"
# Write_Command = "AT+CSCLK=2\r\n"
# Execution_Command = "AT+CSCLK\r\n"


#SMS commands
# phone number
# numb = "+41791384875"
# cmgf = "AT+CMGF=1\r\n"
# cscs = "AT+CSCS=\"GSM\"\r\n"
# cmsg = "AT+CMGS=\"" + numb + "\"\r"
# esc = "\x1a"


#*********End Sim7670E Setup***********

def debug_print(*args):
    global DEBUG
    """Print debug messages if debugging is enabled."""
    if DEBUG:
        print(*args)
        
        
def get_temps():
    global mcp
    try:
        ambient, thermocouple = str(mcp.ambient_temperature), str(mcp.temperature)
    except:
        ambient, thermocouple = "i2c error", "i2c error"
    return ambient, thermocouple

def get_temps_thr(thr):
    global mcp
    try:
        ambient, thermocouple = mcp.ambient_temperature, mcp.temperature
        if thermocouple >= thr:
            return True
        else:
            return False
    except:
        return False

def get_time():
    debug_print("8")
    datetime = system_rtc.datetime()
    print(datetime)
    return datetime[0], datetime[1], datetime[2], datetime[3], datetime[4], datetime[5], datetime[6], 335



#send at without \r\n
def send_at(cmd, back, timeout=7000, forced_delay=0):
    answer = True
    nothing_received = 100 #if nothing has been received for .1 seconds, it will exit the while loop and it will stay max 7 seconds in there
    rec_buff = b''
    Pico_SIM7670E.write((cmd).encode())
    if forced_delay > 0:
        time.sleep(forced_delay)
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


def upload_step_sms(ambient, thermocouple):
    debug_print("4")
    global numb, upload_state, data,last_upload_time, upload_step_time, last_upload_time_holder, sleeping, upload_success

    try:
        current_time = utime.time()
        if upload_state == 0:
            if not send_at("AT\r\n", "OK"):
                upload_success = False
                print(upload_success)
            last_upload_time_holder = current_time
        elif upload_state == 1:
            if not send_at("AT+CSQ\r\n", "OK"):
                upload_success = False
                print(upload_success)
        elif upload_state == 2:
            if not send_at("AT+COPS?\r\n", "OK"):
                upload_success = False
                print(upload_success)
        elif upload_state == 3:
            if not send_at("AT+CNMP=2\r\n", "OK"):
                upload_success = False
                print(upload_success)
        elif upload_state == 4:
            if not send_at("AT+CSCS=\"GSM\"\r\n", "OK"):
                upload_success = False
                print(upload_success)
        elif upload_state == 5:
            if not send_at("AT+CNSMOD?\r\n", "OK"):
                upload_success = False
                print(upload_success)       
        elif upload_state == 6:
            if not send_at("AT+CMGF=1\r\n", "OK"):
                upload_success = False
                print(upload_success)
        elif upload_state == 7:
            send_at("AT+CMGS=\"" + numb + "\"\r", "OK", timeout = 1000)#,forced_delay=1)
#             if not send_at("AT+CMGS=\"" + numb + "\"\r", "OK"):
#                 upload_success = False
#                 print(upload_success)
        elif upload_state == 8:
            if not send_at("Ambient: " + ambient + "\n" + "Thermocouple: " + thermocouple + "\x1a", "OK"):
                upload_success = False
                print(upload_success)      
            
#         #### END SMS, start HTTP           
#         elif upload_state == 6:
#             if not send_at("AT+HTTPINIT", "OK"):
#                 upload_success = False
#                 print(upload_success)
#         elif upload_state == 7:                          # Attempt to upload data
#             if not send_at(f"{HTTPPARA}{url}\"", 'OK'):
#                 upload_success = False
#                 print(upload_success)
#         elif upload_state == 8:
#             if not send_at("AT+HTTPPARA=\"CONTENT\",\"application/json\"", 'OK'):
#                 upload_success = False
#                 print(upload_success)
#         elif upload_state == 9:
#             if not send_at(f"AT+HTTPDATA={len(thinksdata)},1000", "OK"):
#                 upload_success = False
#                 print(upload_success)
#             if not send_at(thinksdata, "OK"):
#                 upload_success = False
#                 print(upload_success)
#         elif upload_state == 10:
#             if not send_at(HTTPACTION_POST, 'OK'):
#                 upload_success = False
#                 print(upload_success)
#         elif upload_state == 11:
#             if not send_at(HTTPHEAD, 'OK'):
#                 upload_success = False
#                 print(upload_success)
#             else:
#                 upload_success = True
#                 if blink:
#                     for i in range (10):
#                         led.toggle()
#                         time.sleep(0.2)
#         elif upload_state == 12:
#             if not send_at("AT+HTTPTERM", "OK"):
#                 upload_success = False
#                 print(upload_success)
#             
            if upload_success:
                # Reset state and clean up after successful upload
                upload_state = 0
                sleeping = False
                upload_success = True
                
                # Get the time the uploading process started
                last_upload_time = last_upload_time_holder
                
#                 #reset the json data
#                 data = {
#                     "write_api_key": APIkey,
#                     "updates": []
#                 }
                
                #collect garbage
                gc.collect()
                print("Upload sequence completed!")
                return  # Exit the function when done
            
            else:
                # Retry or handle failure
                gc.collect()
                upload_state = 0
                upload_success = True
                print("ES HET nöd funktioniert")
                print("Upload failed. Retrying...")
                return
            
        else:
            print("Invalid upload state encountered. Resetting...")
            upload_state = 0  # Reset state
            upload_success = True
            return
        

        # Move to the next state
        upload_state += 1

    except MemoryError:
        # Handle low-memory situations
        gc.collect()
        print("MemoryError: Garbage collection triggered.")

    except Exception as e:
        # Log unexpected errors for debugging
        print(f"Unexpected error in upload_step: {e}")
        upload_state = 0  # Reset state to avoid getting stuck


def read_and_upload():
    debug_print("3")
    
    global data, upload_step_time  # Ensure the global `data` is accessible for updates
    
    # Define the delay between commands (in seconds)
    delay = 0.5
    
    try:
        # Get the current time
        current_time = utime.time()

        # Check if it's time to move to the next step
        if current_time - upload_step_time >= delay:
            # Initiate the upload process
            ambient, thermocouple = get_temps()
            upload_step_sms(ambient, thermocouple)
            upload_step_time = current_time
    
    except Exception as e:
        print(f"Unexpected error: {e}")



while True:
    try:
        current_time_mainloop = utime.time()
        
        #Create a new json file every day
        now = get_time()
        current_day = (now[0], now[1], now[2])
        if current_day != last_upload_day:
#             append_to_csv_file([])
#             createfile()
            last_upload_day = current_day
        
#         # Check if we need to update the JSON file
#         if current_time_mainloop - last_update_time >= updateperiod:
#             updatejson()
#         
        #Check if we want to upload the json file
        if (current_time_mainloop - last_upload_time >= uploadperiod) or ((current_time_mainloop - last_upload_time >= uploadperiod_thr) and get_temps_thr(temp_thr)):
            read_and_upload()

#         
#         if not sleeping:
#             sleepmode()
        
        
#         #Limit the size of the "updates" List
#         entries_updates = data.get("updates", [])
#         if len(entries_updates) > max_entries:
#             del entries_updates[:len(entries_updates) - max_entries]
    
    except MemoryError:
        # Handle low-memory situations
        gc.collect()
        print("MemoryError: Garbage collection triggered.")
    
    
    except Exception as e:
        # Log unexpected errors for debugging
        gc.collect()
        print(f"Unexpected error: {e}")

    # Add a short sleep to prevent tight looping
    time.sleep(0.5)
    led.toggle()