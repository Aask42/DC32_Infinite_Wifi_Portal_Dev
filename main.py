from machine import I2C, Pin, Timer
import gc
import uasyncio as asyncio
from src.ble_sync import BLESync
from src.wifi_manager import WiFiConnection
from src.mqtt_manager import MQTTManager
from CONFIG.MQTT_CONFIG import MQTT_USERNAME, MQTT_PASSWORD, MQTT_CLIENT_ID, MQTT_SERVER
from src.matrix_functions.matrix_manager import MatrixManager
from src.led_controller import LEDController
from src.state_manager import StateManager
from src.animations import AnimationManager
from examples.conways_game import generate_conway_frames
from CONFIG.LED_MANAGER import WS_PWR_PIN, LED_PIN, NUM_LEDS, BRIGHTNESS, HUE_INCREMENT, MAX_COLOR_CYCLE

WS_PWR_PIN = 18
p_ws_leds = Pin(WS_PWR_PIN, Pin.OUT)
p_ws_leds.value(1)

def update_display(t, led_matrix, state_manager):
    frame, delay = state_manager.get_current_frame()
    if frame:
        led_list = state_manager._convert_64bit_to_frame(frame)
        led_matrix.set_led_list(led_list)
    gc.collect()

def update_strip(t, led_controller):
    led_controller.update_strip(t)
    gc.collect()

def reset_motion_flag(t):
    motion_sensor_manager.z_motion = False

def sensor_timer_callback(t, motion_sensor_manager, state_manager, led_controller):
    motion_sensor_manager.update_readings()
    state_manager.update_motion_state(motion_sensor_manager)

    if motion_sensor_manager.z_history[-1] < -10 and not motion_sensor_manager.upsidedown:
        motion_sensor_manager.upsidedown = True
        print("I'm upsidedown!")
        led_controller.smooth_brightness_transition(10)

    if motion_sensor_manager.z_history[-1] > 2 and motion_sensor_manager.z_history[0] > 1 and motion_sensor_manager.upsidedown:
        motion_sensor_manager.upsidedown = False
        print("I'm right side up!")
        led_controller.smooth_brightness_transition(100)

def trigger_on_beat(t, led_controller):
    led_controller.update_direction()

def ble_timer_callback(t, ble_sync):
    ble_sync.sync_frames(t)
    gc.collect()

def sub_cb(topic, msg, direction_timer, display_timer, state_manager, led_controller):
    msg_string = msg.decode("UTF-8")
    print(f"Received message: {msg} on topic: {topic.decode()} ")
    if topic == b'bpm':
        state_manager.current_frame_index = 0
        led_controller.cycle = 0
        bpm = int(int(msg_string) * 1.00)
        direction_timer.init(period=int(60000 / bpm), mode=Timer.PERIODIC, callback=lambda t: trigger_on_beat(t, led_controller))
        display_timer.init(freq=int(bpm/4), mode=Timer.PERIODIC, callback=lambda t: update_display(t, led_matrix, state_manager))

async def main():
    gc.enable()
    led_controller = LEDController(NUM_LEDS, LED_PIN, 100, 20.0/360.0, MAX_COLOR_CYCLE)
    led_controller.set_brightness(50)

    i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
    state_manager = StateManager()
    matrix_manager = MatrixManager(state_manager, i2c)
    global led_matrix
    led_matrix = matrix_manager.led_matrix

    # Initialize timers and other components
    frame_generator = matrix_manager.scroll_text_frames("_THE_32nd_DEF~CON_IS_CANCELLED_", delay=0.05)
    for frame, delay in frame_generator:
        state_manager.add_frame(frame, delay)

    frame_timer = Timer(1)
    frame_timer.init(freq=7, mode=Timer.PERIODIC, callback=lambda t: update_strip(t, led_controller))

    display_timer = Timer(2)
    display_timer.init(freq=15, mode=Timer.PERIODIC, callback=lambda t: update_display(t, led_matrix, state_manager))

    direction_timer = Timer(3)
    bpm = 60
    direction_timer.init(period=int(60000 / bpm), mode=Timer.PERIODIC, callback=lambda t: trigger_on_beat(t, led_controller))

    # Initialize WiFi and MQTT managers
    wifi_manager = WiFiConnection()
    await wifi_manager.main()

    mqtt_manager = MQTTManager(MQTT_SERVER, MQTT_CLIENT_ID, MQTT_USERNAME, MQTT_PASSWORD)
    await mqtt_manager.main(wifi_manager)  # Ensure the MQTT waits for WiFi connection
    mqtt_manager.set_callback(lambda topic, msg: sub_cb(topic, msg, direction_timer, display_timer, state_manager, led_controller))

    await mqtt_manager.subscribe(b'bpm')

    while True:
        await asyncio.sleep(30)
        gc.collect()

asyncio.run(main())
