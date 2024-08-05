from machine import I2C, Pin, Timer
import time
import gc
from src.matrix_functions import matrix_setup  # Assuming matrix_setup.py is in the same directory
from src.led_controller import LEDController

from src.animations import AnimationManager

from CONFIG.LED_MANAGER import WS_PWR_PIN, LED_PIN, NUM_LEDS, BRIGHTNESS, HUE_INCREMENT, MAX_COLOR_CYCLE

WS_PWR_PIN = 18
p_ws_leds = Pin(WS_PWR_PIN, Pin.OUT)
p_ws_leds.value(1)

class StateManager:
    def __init__(self):
        self.frames = []
        self.current_frame_index = 0

    def add_frames(self, frames):
        self.frames.extend(frames)

    def get_current_frame(self):
        if self.frames:
            if self.current_frame_index >= len(self.frames):
                self.current_frame_index = 0
            frame, _ = self.frames[self.current_frame_index]
            self.current_frame_index = (self.current_frame_index + 1) % len(self.frames)
            return frame
        return None

def update_display(t):
    frame = state_manager.get_current_frame()
    if frame:
        led_matrix.set_led_list(frame)

def update_strip(t):
    global led_controller, led_matrix
    led_controller.update_strip(t)

def main():
    global led_matrix, state_manager, led_controller
    
    # Initialize I2C and the LED matrix
    i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
    led_matrix = matrix_setup.set_up_led_matrix(i2c)

    # Create instances
    state_manager = StateManager()
    animation_manager = AnimationManager()

    frames = []
    # Generate frames and add them to the state manager
    animations = [
        animation_manager.convert_to_matrix_map(animation_manager.generate_sine_wave(50, frequency=5)), 
        animation_manager.generate_eq_frames(20), 
        animation_manager.convert_to_matrix_map(animation_manager.jump_man_frames),
        animation_manager.convert_to_matrix_map(animation_manager.flashy)
    ]
    for animation in animations:
        frames += animation
    state_manager.add_frames(frames)

    led_controller = LEDController(NUM_LEDS, LED_PIN, 255, 20.0/360.0, MAX_COLOR_CYCLE)
    led_controller.set_brightness(30)

    frame_timer = Timer(1)
    frame_timer.init(freq=15, mode=Timer.PERIODIC, callback=update_strip)

    # Start the display update timer
    display_timer = Timer(2)
    display_timer.init(freq=15, mode=Timer.PERIODIC, callback=update_display)

    # Start the beat trigger timer
    direction_timer = Timer(3)
    bpm = 60  # Example BPM
    direction_timer.init(period=int(60000 / bpm), mode=Timer.PERIODIC, callback=lambda t: animation_manager.trigger_on_beat(t, state_manager, led_controller))

main()
