import machine
from machine import Pin, I2C, Timer
import uasyncio
from led_controller import LEDController
from mqtt_manager import MQTTManager
from wifi_manager import WiFiConnection
from lib.ble_sync import BLESync  # Make sure the path is correct
from matrix_functions.matrix_setup import set_up_led_matrix
from matrix_functions.matrix_functions import fading_strobe_matrix, display_number
from CONFIG.LED_MANAGER import NUM_LEDS, LED_PIN, BRIGHTNESS, HUE_INCREMENT, MAX_COLOR_CYCLE, WS_PWR_PIN
from CONFIG.MQTT_CONFIG import MQTT_SERVER, MQTT_CLIENT_ID, MQTT_USERNAME, MQTT_PASSWORD
from CONFIG.CLOCK_CONFIG import NTP_SERVER, TIMEZONE_OFFSET, DAYLIGHT_SAVING
from CONFIG.BLE_CONFIG import ble_role
import ntptime
import utime
from LTR_308ALS import LTR_308ALS  # Import the LTR-308ALS library

frame_number = 0
p_ws_leds = Pin(WS_PWR_PIN, Pin.OUT)
p_ws_leds.value(1)

# Initialize I2C for the ambient light sensor
i2c = I2C(0, scl=Pin(22), sda=Pin(21))  # Adjust the pins according to your setup
light_sensor = LTR_308ALS(i2c, gain=1)

led_controller = LEDController(NUM_LEDS, LED_PIN, BRIGHTNESS, HUE_INCREMENT, MAX_COLOR_CYCLE)
ble_sync = None

matrix_brightness = 100

frame_number = 0
def get_time():
    return utime.localtime()

async def set_time():
    global timezone_offset_sync
    ntptime.host = NTP_SERVER
    try:
        cur_time = get_time()
        print("Local time before synchronization: %s" % str(get_time()))
        ntptime.settime()
        new_time = get_time()
        if  new_time[6]-cur_time[6] > 1:
            timezone_offset_sync = cur_time[6]-new_time[6]
        else:
            timezone_offset_sync = 0
        print("Local time after synchronization: %s" % str(get_time()))
    except Exception as e:
        print("Error syncing time:", e)

async def ble_time_sync():
    global ble_sync
    ble_sync = BLESync()
    ble_sync.ble_role = ble_role
    await uasyncio.create_task(ble_sync.run())

def sub_cb(topic, msg):
    global direction_timer, ble_sync, frame_number
    msg_string = msg.decode("UTF-8")
    print(f"Received message: {msg} on topic: {topic.decode()} at current frame: {frame_number}")
    if topic == b'bpm':
        while utime.time_ns() % 10 !=0:
            continue
        bpm = int(int(msg_string) * 1.02)
        direction_timer.init(period=int(60000 / bpm), mode=Timer.PERIODIC, callback=change_direction)

def update_strip(t):
    led_controller.update_strip(t)
count = 0

def change_direction(t):
    global count  # Declare count as global
    global led_matrix, matrix_brightness
    
    # Also pulse the back matrix
    #uasyncio.create_task(fading_strobe_matrix(led_matrix=led_matrix, max_brightness=100))
    print(f"Attempting to display number {count}")
    uasyncio.create_task(display_number(number=count, led_matrix=led_matrix, steps=2))
    led_controller.update_direction()
    
    # Increment count and reset if necessary
    count += 1
    if count > 9:
        count = 0
    

# Function to read ambient light and adjust brightness
async def adjust_brightness():
    global matrix_brightness, ble_sync, frame_number
    while True:
        if ble_sync and ble_role == "peripheral":
            led_controller.frame_count = ble_sync.frame_count
        elif ble_sync:
            ble_sync.frame_count = led_controller.frame_count  # Update BLE frame count
        frame_number = led_controller.frame_count
        lux = light_sensor.getdata()
        matrix_brightness = min(max(int(lux / 10), 20), 255)
        brightness = min(max(int(lux / 10), 40), 255)  # Map lux to brightness (0-255)
        led_controller.set_brightness(brightness)  # Adjust NeoPixel brightness
        # Adjust matrix brightness here if needed
        await uasyncio.sleep_ms(100)  # Adjust every second

frame_timer = Timer(1)
frame_timer.init(period=100, mode=Timer.PERIODIC, callback=update_strip)

async def main():
    global led_matrix, direction_timer
    led_matrix = set_up_led_matrix(i2c=i2c)
    uasyncio.create_task(ble_time_sync())
    uasyncio.create_task(adjust_brightness())  # Start the brightness adjustment task

    wifi_connection = WiFiConnection()
    uasyncio.create_task(wifi_connection.main())
    mqtt_manager = None
    
    mqtt_tries = 0
    mqtt_max_tries = 3
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
                    uasyncio.create_task(mqtt_manager.check_messages())
                    
            else:
                break
        direction_timer = Timer(2)
        bpm = int(128 * 1.02)
        direction_timer.init(period=int(60000 / bpm), mode=Timer.PERIODIC, callback=change_direction)
        #print(f"{utime.time_ns()}")
        await uasyncio.sleep_ms(1)
    while True:
        #print(f"{frame_number}")

        await uasyncio.sleep_ms(1)

uasyncio.run(main())

