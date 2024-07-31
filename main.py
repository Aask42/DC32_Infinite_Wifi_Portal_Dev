import machine
from machine import Pin, Timer
import uasyncio 
from CONFIG.LED_MANAGER import NUM_LEDS, LED_PIN, BRIGHTNESS, STARTING_ANIMATION, MAX_COLOR_CYCLE, HUE_INCREMENT, WS_PWR_PIN
from led_controller import LEDController
from mqtt_manager import MQTTManager
from CONFIG.MQTT_CONFIG import MQTT_SERVER, MQTT_CLIENT_ID, MQTT_USERNAME, MQTT_PASSWORD
from matrix_functions.matrix_setup import set_up_led_matrix
from matrix_functions.matrix_functions import fading_strobe_matrix
import ntptime
from wifi_manager import WiFiConnection

from lib.ble_sync import BLESync

from CONFIG.CLOCK_CONFIG import NTP_SERVER, TIMEZONE_OFFSET, DAYLIGHT_SAVING
from CONFIG.BLE_CONFIG import ble_role

import utime

frame_number = 0
# Power control for the LED strip
p_ws_leds = Pin(WS_PWR_PIN, Pin.OUT)
p_ws_leds.value(1)  # Turn on power to the LED strip

# Initialize LED controller
led_controller = LEDController(NUM_LEDS, LED_PIN, BRIGHTNESS, HUE_INCREMENT, MAX_COLOR_CYCLE)

def get_time():
    return utime.localtime()

async def set_time():
    global timezone_offset_sync
    ntptime.host = NTP_SERVER
    #while True:
    try:
        cur_time = get_time()
        print("Local time before synchronization: %s" % str(get_time()))
        
        # Make sure to have internet connection
        ntptime.settime()
        new_time = get_time()
        if  new_time[6]-cur_time[6] > 1:
            #we got ahead, need to go back
            #adjust things to sync with the offset
            timezone_offset_sync = cur_time[6]-new_time[6]
        else:
            timezone_offset_sync = 0

        print("Local time after synchronization: %s" % str(get_time()))
    except Exception as e:
        print("Error syncing time:", e)
    #await uasyncio.sleep(60)
        
# BLE Time sync
ble_sync = None
async def ble_time_sync():
    global ble_sync
    ble_sync = BLESync()
    await uasyncio.create_task(ble_sync.run())
 
# Define the callback function for MQTT messages
def sub_cb(topic, msg):
    global bpm, direction_timer
    msg_string = msg.decode("UTF-8")
    print(f"Received message: {msg} on topic: {topic.decode()}")
    
    if topic == b'bpm':
        #uasyncio.create_task(set_time())
        
        while int(utime.time_ns()) % (led_controller.frame_count * 1000000) > 10000:
            continue
        bpm = int(int(msg_string) * 1.02)  # Beats per minute
        
        direction_timer.init(period=int(60000 / bpm), mode=Timer.PERIODIC, callback=change_direction)

# Function to update the strip
def update_strip(t):
    led_controller.update_strip(t)

# Function to change direction
def change_direction(t):
    global led_matrix
    if ble_sync.frame_count < led_controller.frame_count:
        
        ble_sync.frame_count = led_controller.frame_count
    else:
        print("Fast forwarding to frame {led_controller.frame_count}")
        led_controller.frame_count = ble_sync.frame_count
    uasyncio.create_task(fading_strobe_matrix(led_matrix=led_matrix))
    led_controller.update_direction()
    

# Start the timer with a shorter interval for smoother animation
frame_timer = Timer(1)
frame_timer.init(period=100, mode=Timer.PERIODIC, callback=update_strip)


async def main():
    global led_matrix, direction_timer
    
    led_matrix = set_up_led_matrix()  # Initialize the LED matrix
    
    uasyncio.create_task(ble_time_sync())
    
    mqtt_manager = None
    
    wifi_connection = WiFiConnection()
    uasyncio.create_task(wifi_connection.main())
    while True:
        if wifi_connection.wifi_connected:
            uasyncio.create_task(set_time())

            if mqtt_manager is None:
                print("Connecting to MQTT")
                mqtt_manager = MQTTManager(MQTT_SERVER, MQTT_CLIENT_ID, MQTT_USERNAME, MQTT_PASSWORD)
                mqtt_manager.set_callback(sub_cb)
            
            if not mqtt_manager.mqtt_connected:
            
                mqtt_manager.connect()

                if mqtt_manager.mqtt_connected:
                    mqtt_manager.subscribe(b'bpm')
                    # Start the task to check for incoming MQTT messages
                    uasyncio.create_task(mqtt_manager.check_messages())
            else:
                break
        # Timer to change direction based on BPM
        direction_timer = Timer(-1)
        bpm = int(128 * 1.02)  # Beats per minute
        direction_timer.init(period=int(60000 / bpm), mode=Timer.PERIODIC, callback=change_direction)

        await uasyncio.sleep_ms(1)
    while True:
        await uasyncio.sleep_ms(1)

uasyncio.run(main())

