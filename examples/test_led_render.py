# Draw a box on the edge of the display.
#
import math
import time
from micropython import const

from machine import Pin, I2C
from lib.IS31FL3729 import IS31FL3729



i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

led_matrix = IS31FL3729(i2c)

def step_through_leds():
    for reg in range(0,46):
        for i,item in enumerate(led_matrix.led_brightness_map):
            for led in led_matrix.led_matrix_map:
                register = led_matrix.led_matrix_map[led]
                
                print(f"existing coords: {item}, reg: {register}, step: {reg}, x,y {led}")
        led_matrix.set_led(reg, 255)
        
        hit_enter = input(f"You are on hex address {reg} Hit ENTER to continue")
        
        time.sleep_ms(10)
        
    for reg in reversed(range(0,46)):
        led_matrix.set_led(reg, 0)
        #hit_enter = input(f"You are on hex address {reg} Hit ENTER to continue")
        time.sleep_ms(10)

def water_wave(brightness=100, delay=0.1):
    delay = 67
    wave_pattern = [
        [0, 1, 2, 1, 0, 0],
        [1, 2, 3, 2, 1, 0],
        [2, 3, 4, 3, 2, 0],
        [3, 4, 5, 4, 3, 0],
        [4, 5, 6, 5, 4, 0],
        [5, 6, 5, 4, 3, 0],
        [4, 5, 4, 3, 2, 0]
    ]
    
    while True:
        # Forward wave
        for col_offset in range(6):
            led_list_x_y = []
            for row in range(6):
                for col in range(5):
                    adj_col = col + col_offset
                    if adj_col < 6:
                        brightness_value = brightness if wave_pattern[row][col] >= 3 else 0
                        led_list_x_y.append((row, adj_col, brightness_value))
            led_matrix.set_led_list(led_list_x_y)
            time.sleep_ms(delay)
        
        # Backward wave
        for col_offset in range(6, -1, -1):
            led_list_x_y = []
            for row in range(6):
                for col in range(5):
                    adj_col = col + col_offset
                    if adj_col < 6:
                        brightness_value = brightness if wave_pattern[row][col] >= 3 else 0
                        led_list_x_y.append((row, adj_col, brightness_value))
            led_matrix.set_led_list(led_list_x_y)
            time.sleep_ms(delay)

# Example animation loop
while True:
    #led_matrix.water_wave()
    water_wave(100)
    #step_through_leds()




