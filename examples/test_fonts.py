import math
import time
from machine import Pin, I2C
import random
from lib.IS31FL3729 import IS31FL3729
from infinity_mirror_font import number_patterns, char_patterns, char_patterns_lower

# Initialize the I2C bus and IS31FL3729 driver
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
display = IS31FL3729(i2c)

# Function to display a pattern on the LED matrix with fade-in effect
def display_pattern_with_fade(pattern):
    steps = 50  # Number of steps for fade-in
    delay = 0.005  # Delay between steps

    for step in range(steps + 1):
        brightness_scale = step / steps
        led_list = []
        for x, row in enumerate(pattern):
            for y, val in enumerate(row):
                brightness = int(100 * brightness_scale) if val == 1 else 0
                led_list.append((x, y, brightness))
        display.set_led_list(led_list)
        time.sleep(delay)

# Test program to cycle through characters and numbers with fade-in effect
def test_display():
    while True:
        # Display characters in alphabetical order
        for char in sorted(char_patterns.keys()):
            pattern = char_patterns[char]
            print(f"Displaying character: {char}")
            display.clear_matrix()
            display_pattern_with_fade(pattern)
            time.sleep(1)

        # Display lowercase characters in alphabetical order
        for char in sorted(char_patterns_lower.keys()):
            pattern = char_patterns_lower[char]
            print(f"Displaying lowercase character: {char}")
            display.clear_matrix()
            display_pattern_with_fade(pattern)
            time.sleep(1)

        # Display numbers in numerical order
        for num in sorted(number_patterns.keys()):
            pattern = number_patterns[num]
            print(f"Displaying number: {num}")
            display.clear_matrix()
            display_pattern_with_fade(pattern)
            time.sleep(1)

# Run the test program
test_display()
