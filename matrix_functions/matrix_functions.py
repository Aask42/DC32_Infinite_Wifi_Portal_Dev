"""
Written by: BadAask
Written for: DC32
Date started: 20240726
Copyright: Do what you want because a pirate is free

Description: This function provides helper functions for interacting with an x,y grid based set of frames. 
It was originally written for the IS31FL3729 chip but can be used for any led_matrix obj that has the functions
set_led_list and clear_matrix, and defines its rows and cols, You can set up set_led_list and clear_matrix 
for your specific X by Y display you wish to use. 

NOTE: This is only written for a SINGLE COLOR display and does not handle multiple
"""

import uasyncio
import math
from matrix_functions.infinity_mirror_font import number_patterns, char_patterns, char_patterns_lower, punctuation_patterns

async def display_number(number, fade_time=0.5, steps=15, led_matrix=None):
   
    rows = led_matrix.rows
    cols = led_matrix.cols
    
    pattern = number_patterns[int(number)]  # Convert to integer here
    for step in range(steps + 1):
        brightness = int((math.sin(math.pi * step / steps) ** 2) * 100)
        led_list_x_y = []
        for x in range(rows):
            for y in range(cols):
                led_list_x_y.append((x, y, brightness if pattern[x][y] == 1 else 0))
        led_matrix.set_led_list(led_list_x_y)
        await uasyncio.sleep(fade_time / steps)
        
def get_char_pattern(char):
    if char.isdigit():
        return number_patterns.get(int(char), [[0]*6]*7)
    elif char.isupper():
        return char_patterns.get(char, [[0]*6]*7)
    elif char in punctuation_patterns:
        return punctuation_patterns[char]
    else:
        return char_patterns_lower.get(char, [[0]*6]*7)

async def scroll_text(text="DC32", delay=0.1, led_matrix=None):
    led_matrix.clear_matrix()
    buffer = [[0] * (6 * len(text)) for _ in range(7)]
    
    # Create a buffer with all characters side by side
    for i, char in enumerate(text):
        pattern = get_char_pattern(char)
        for x in range(7):
            for y in range(6):
                buffer[x][i*6 + y] = pattern[x][y]

    # Scroll the buffer
    for offset in range(len(buffer[0]) - 6 + 1):
        led_list = []
        for x in range(7):
            for y in range(6):
                brightness = 255 if buffer[x][y + offset] == 1 else 0
                led_list.append((x, y, brightness))
        led_matrix.set_led_list(led_list)
        await uasyncio.sleep(delay)

async def fading_strobe_matrix(max_brightness=100, steps=5, fade_delay = 10, led_matrix = None):
    
    if not led_matrix:
        print("No LED Matrix provided")
        return -1
    #global tick
    """
    Fading strobe function for the LED matrix.

    Args:
        led_driver (IS31FL3729): The LED driver instance.
        max_brightness (int): The maximum brightness value to fade up to.
        steps (int): The number of steps to take for fading.

    Usage:
        led_driver = IS31FL3729(i2c)
        fading_strobe(led_driver, 255, 20)
    """
    for i in range(steps):
        brightness = int(max_brightness * (i / steps))
        led_matrix.set_led_list([(x, y, brightness) for x in range(led_matrix.rows) for y in range(led_matrix.cols)])
        await uasyncio.sleep_ms(fade_delay)  # Adjust the delay as needed
    await uasyncio.sleep_ms(10)  # Adjust the delay as needed
    for i in range(steps, 0, -1):
        brightness = int(max_brightness * (i / steps))
        led_matrix.set_led_list([(x, y, brightness) for x in range(led_matrix.rows) for y in range(led_matrix.cols)])
        await uasyncio.sleep_ms(fade_delay)  # Adjust the delay as needed
    led_matrix.set_led_list([(x, y, 0) for x in range(led_matrix.rows) for y in range(led_matrix.cols)])

    await uasyncio.sleep_ms(10)  # Adjust the delay as needed
