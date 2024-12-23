import machine
import sdcard
import uos
import json
import os
import requests
import time
import utime
import gc
import urtc
from hx711 import *

#enable garbage collector
gc.enable()

#turn on and off debugging, use: debug_print() for debugging
DEBUG = False

#blinking when uploading
blink = True

if blink:
    led = machine.Pin(25, machine.Pin.OUT)

#*********Start RTC Setup***********
i2c = machine.I2C(id = 0, scl=machine.Pin(5), sda=machine.Pin(4))
rtc = urtc.PCF8523(i2c)


#set pico rtc simmilar to rtc to external RTC
datetime = rtc.datetime()
system_rtc = machine.RTC()
system_rtc.datetime((
    datetime.year, datetime.month, datetime.day, 
    datetime.weekday, datetime.hour, datetime.minute, datetime.second, 0
))
#*********End RTC Setup***********

#Variables
APIkey = "QUP42CU3RK1X6R2Z"                                                           #*****************               Update personal APIkey                    **************************
Channel = "2716690"                                                                   #*****************                  Update Channel ID                      **************************
updateperiod = 5                                                                      #*****************        Update how often your sensors take samples       **************************
amount_samples = 10                                                                   #*****************     After how many samples do you want to save it to the SD card    **************************
uploadperiod = 20                                                                     #*****************   Update how often the data is uploaded to thinkspeak (lowest that is useful is 20sec)   **************************
max_entries = 200                                                                     #*****************      adjust the max amount of entries in Updates        **************************
url = "http://api.thingspeak.com/channels/"+ Channel +"/bulk_update.json"

data = {
    "write_api_key": APIkey,
    "updates": [
    ]
}

last_upload_day = None
update_counter = 0
collected_data = []
upload_state = 0  # Global state variable
last_upload_time = utime.time()  # Tracks the time of the last step
last_update_time = utime.time()
last_update_time_holder = utime.time()
upload_step_time = utime.time()
sleeping = False
upload_success = True

#*********Start Loadcell Setup***********
tare_value = 82277.0
calibration_factor = 4.276765e-05
hx = hx711(machine.Pin(6), machine.Pin(7))
hx.set_power(hx711.power.pwr_up)
hx.set_gain(hx711.gain.gain_128)
hx711.wait_settle(hx711.rate.rate_10)
#*********End Loadcell Setup***********

#*********Start Thermocouple Setup***********
# Create an ADC object on pin 26 (ADC0), which corresponds to physical pin 32 on the Pico
ad8495 = machine.ADC(26)
 
# Constants for calculations
VREF = 3.3  # Reference voltage for the Pico ADC
ADC_RESOLUTION = 65535  # 16-bit ADC resolution
#*********End Thermocouple Setup***********

#*********Start SD Setup***********
# Assign chip select (CS) pin (and start it high)
cs = machine.Pin(9, machine.Pin.OUT)

# Intialize SPI peripheral (start with 1 MHz)
spi = machine.SPI(1,
                  baudrate=1000000,
                  polarity=0,
                  phase=0,
                  bits=8,
                  firstbit=machine.SPI.MSB,
                  sck=machine.Pin(10),
                  mosi=machine.Pin(11),
                  miso=machine.Pin(8))

# Initialize SD card
headers = ["Timestamp", "Weight[kg]", "Temperature"]                               #*****************           Change names of headers in CSV             **************************
sd = sdcard.SDCard(spi, cs)

# Create a filename
basepath = "/sd/"
filename = "DAY"
ext = ".csv"
num = "0001"
collector = "collector"


# Mount filesystem
try:
    vfs = uos.VfsFat(sd)
    uos.mount(vfs, "/sd")
    
except Exception as e:
    print(f"SD Card error: {e}")
#*********End SD Setup***********


#*********Start Sim7670E Setup***********
# uart setting
uart_port = 0
uart_baute = 115200
Pico_SIM7670E = machine.UART(uart_port, uart_baute)


#HTTP commands
HTTPINIT = "AT+HTTPINIT"
HTTPPARA = "AT+HTTPPARA=\"URL\",\""
HTTPACTION_GET = "AT+HTTPACTION=0"
HTTPACTION_POST = "AT+HTTPACTION=1"
HTTPHEAD = "AT+HTTPHEAD"
HTTPTERM = "AT+HTTPTERM"

#sleepmode commands
Read_Command = "AT+CSCLK?"
Test_Command = "AT+CSCLK=?"
Write_Command = "AT+CSCLK=2"
Execution_Command = "AT+CSCLK"
#*********End Sim7670E Setup***********

# Send AT command
def send_at(cmd, back, timeout=7000):
    answer = False
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


# Checks if this file exists
def exists(filepath):
    try:
        f = open(filepath, "r")
        # continue with the file.
        return True
    except OSError:  # open failed
       # handle the file open case
       return False

def createfile():
    debug_print("1")
    """Create a file with a unique name."""
    global num, headers  # To modify the global `num` variable
    filepath = f"{basepath}{filename}{num}{collector}{ext}"
    while exists(filepath):
        num = f"{int(num) + 1 :04d}"  # Increment and format `num`
        filepath = f"{basepath}{filename}{num}{collector}{ext}"  # Update the filepath
        
    with open(f"{basepath}{filename}{num}{collector}{ext}", mode="w") as cfile:
        header_line = ",".join(headers) + "\n"
        cfile.write(header_line)  # Write the header row




def updatejson():
    debug_print("2")
    global last_update_time
    collector_filepath = f"{basepath}{filename}{num}{collector}{ext}"
    now = get_time()
    timestr = "{}-{}-{} {}:{}:{} +0100".format(now[0], now[1], now[2],now[3], now[4],now[5])
    last_update_time = utime.time()

    if now[5] != 59:
        incr = now[5] + 1
    else:
        incr = 0
    
    value1 = get_weight()                                                                              #***************** add sensor Values here *********************
    value2 = get_temp()                                                                                #***************** add sensor Values here *********************
    
    new_entry = {
        "created_at": timestr,
        "field1": value1,
        "field2": value2
    }

    # Add the new entry to the "updates" list
    data["updates"].append(new_entry)
    
    append_to_csv_file([timestr, value1, value2])


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
            upload_step(json.dumps(data))
            upload_step_time = current_time
    
    except Exception as e:
        print(f"Unexpected error: {e}")




def upload_step(thinksdata):
    debug_print("4")
    global upload_state, data,last_upload_time, upload_step_time, last_upload_time_holder, sleeping, upload_success

    try:
        current_time = utime.time()
        if upload_state == 0:
            if not send_at("AT", "OK"):
                upload_success = False
                print(upload_success)
            last_upload_time_holder = current_time
        elif upload_state == 1:
            if not send_at("AT+CSQ", "OK"):
                upload_success = False
                print(upload_success)
        elif upload_state == 2:
            if not send_at("AT+COPS?", "OK"):
                upload_success = False
                print(upload_success)
        elif upload_state == 3:
            if not send_at("AT+CNMP=2", "OK"):
                upload_success = False
                print(upload_success)
        elif upload_state == 4:
            if not send_at("AT+CSCS=\"GSM\"", "OK"):
                upload_success = False
                print(upload_success)
        elif upload_state == 5:
            if not send_at("AT+CNSMOD?", "OK"):
                upload_success = False
                print(upload_success)
        elif upload_state == 6:
            if not send_at("AT+HTTPINIT", "OK"):
                upload_success = False
                print(upload_success)
        elif upload_state == 7:                          # Attempt to upload data
            if not send_at(f"{HTTPPARA}{url}\"", 'OK'):
                upload_success = False
                print(upload_success)
        elif upload_state == 8:
            if not send_at("AT+HTTPPARA=\"CONTENT\",\"application/json\"", 'OK'):
                upload_success = False
                print(upload_success)
        elif upload_state == 9:
            if not send_at(f"AT+HTTPDATA={len(thinksdata)},1000", "OK"):
                upload_success = False
                print(upload_success)
            if not send_at(thinksdata, "OK"):
                upload_success = False
                print(upload_success)
        elif upload_state == 10:
            if not send_at(HTTPACTION_POST, 'OK'):
                upload_success = False
                print(upload_success)
        elif upload_state == 11:
            if not send_at(HTTPHEAD, 'OK'):
                upload_success = False
                print(upload_success)
            else:
                upload_success = True
                if blink:
                    for i in range (10):
                        led.toggle()
                        time.sleep(0.2)
        elif upload_state == 12:
            if not send_at("AT+HTTPTERM", "OK"):
                upload_success = False
                print(upload_success)
            
            if upload_success:
                # Reset state and clean up after successful upload
                upload_state = 0
                sleeping = False
                upload_success = True
                
                # Get the time the uploading process started
                last_upload_time = last_upload_time_holder
                
                #reset the json data
                data = {
                    "write_api_key": APIkey,
                    "updates": []
                }
                
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

def sleepmode():
    global sleeping
    if send_at(Write_Command, "OK"):
        sleeping = True
        print("Gute Nacht")

def get_weight():
    debug_print("5")
    for i in range (5):
        hx.get_value()
    weight_f = (hx.get_value() - tare_value) * calibration_factor
    return weight_f

def get_voltage(adc_pin):
    debug_print("6")
    """Convert the ADC reading to voltage."""
    return (adc_pin.read_u16() * VREF) / ADC_RESOLUTION

def get_temp():
    debug_print("7")
    temperature_c = 0
    for i in range (5):
        temperature_c += (get_voltage(ad8495) - 1.25) / 0.005
    return temperature_c/5

def get_time():
    debug_print("8")
    datetime = rtc.datetime()
    return datetime.year, datetime.month, datetime.day, datetime.hour, datetime.minute, datetime.second, datetime.weekday, 335

def debug_print(*args):
    global DEBUG
    """Print debug messages if debugging is enabled."""
    if DEBUG:
        print(*args)

def append_to_csv_file(data_row):
    global amount_samples, update_counter, collected_data
    """
    Appends a single row of data to an existing CSV file.
    :param data_row: List of data entries corresponding to the headers.
    """
    # Add the new data row to the collection
    collected_data.append(data_row)
    print(f"Appended to data collection: {data_row}")
    update_counter += 1
    
    # Write to the CSV file when enough samples are collected
    if update_counter >= amount_samples:
        with open(f"{basepath}{filename}{num}{collector}{ext}", mode="a") as cfile:
            # Write each collected row as a line in the CSV file
            for row in collected_data:
                data_line = ",".join(map(str, row)) + "\n"  # Add newline character
                cfile.write(data_line)
        print(f"Appended to CSV: {collected_data}")
        
        # Reset collection and counter
        collected_data = []  # Clear collected data after writing
        update_counter = 0

    


while True:
    try:
        current_time_mainloop = utime.time()
        
        #Create a new json file every day
        now = get_time()
        current_day = (now[0], now[1], now[2])
        if current_day != last_upload_day:
            append_to_csv_file([])
            createfile()
            last_upload_day = current_day
        
        # Check if we need to update the JSON file
        if current_time_mainloop - last_update_time >= updateperiod:
            updatejson()
        
        #Check if we want to upload the json file
        if current_time_mainloop - last_upload_time >= uploadperiod:
            read_and_upload()
        
        
        if not sleeping:
            sleepmode()
        
        
        #Limit the size of the "updates" List
        entries_updates = data.get("updates", [])
        if len(entries_updates) > max_entries:
            del entries_updates[:len(entries_updates) - max_entries]
    
    except MemoryError:
        # Handle low-memory situations
        gc.collect()
        print("MemoryError: Garbage collection triggered.")
    
    
    except Exception as e:
        # Log unexpected errors for debugging
        gc.collect()
        print(f"Unexpected error: {e}")

    # Add a short sleep to prevent tight looping
    time.sleep(0.1)
        
        
        
        



