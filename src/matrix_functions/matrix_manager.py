from lib.IS31FL3729 import IS31FL3729
from machine import Pin, I2C
import time
import uasyncio as asyncio
import math
from src.matrix_functions.infinity_mirror_font import number_patterns, char_patterns, char_patterns_lower, punctuation_patterns

class MatrixManager:
    def __init__(self, state_manager, i2c=None):
        self.state_manager = state_manager
        self.i2c = i2c if i2c else I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
        self.led_matrix = IS31FL3729(self.i2c)
        self._setup_led_matrix()

    def _setup_led_matrix(self):
        cs_currents = [0x40] * 14
        cs_currents.append(0xff)
        self.led_matrix.cs_currents = cs_currents
        self._create_led_matrix_map()
        self._create_led_brightness_map()
        self.led_matrix.rows = 7
        self.led_matrix.cols = 6
        self.led_matrix.start_display()

    def refresh(self):
        self.led_matrix.render_led_map()

    def _create_led_matrix_map(self):
        self.led_matrix.led_matrix_map = {
            (0, 0): 0x2e, (0, 1): 0x2d, (0, 2): 0x1e, (0, 3): 0x1d, (0, 4): 0x0e, (0, 5): 0x0d, (0, 6): 0x1f,
            (1, 0): 0x2c, (1, 1): 0x2b, (1, 2): 0x1c, (1, 3): 0x1b, (1, 4): 0x0c, (1, 5): 0x0b, (1, 6): 0x0f,
            (2, 0): 0x2a, (2, 1): 0x29, (2, 2): 0x1a, (2, 3): 0x19, (2, 4): 0x0a, (2, 5): 0x09,
            (3, 0): 0x28, (3, 1): 0x27, (3, 2): 0x18, (3, 3): 0x17, (3, 4): 0x08, (3, 5): 0x07,
            (4, 0): 0x26, (4, 1): 0x25, (4, 2): 0x16, (4, 3): 0x15, (4, 4): 0x06, (4, 5): 0x05,
            (5, 0): 0x24, (5, 1): 0x23, (5, 2): 0x14, (5, 3): 0x13, (5, 4): 0x04, (5, 5): 0x03,
            (6, 0): 0x22, (6, 1): 0x21, (6, 2): 0x12, (6, 3): 0x11, (6, 4): 0x02, (6, 5): 0x01
        }

    def _create_led_brightness_map(self):
        self.led_matrix.led_brightness_map = {i: 0 for i in range(0x30)}

    def test_turn_on_all(self, brightness=100):
        for x in range(7):
            for y in range(6):
                address = self.led_matrix.led_matrix_map[(x, y)]
                self.led_matrix.led_brightness_map[address] = brightness
        self.refresh()

    def test_led_matrix(self):
        for item in self.led_matrix.led_matrix_map:
            reg = self.led_matrix.led_matrix_map[item]
            reg_hex = hex(self.led_matrix.led_matrix_map[item])
            print(f"register: {reg_hex} == {reg}, coord: {item}")
            self.led_matrix.set_led_raw(reg, 255)
            time.sleep(1)
            input("Is this correct? If not you should fix it...")
            self.led_matrix.set_led_raw(reg, 0)

    def test_render_led_map(self):
        for x in range(7):
            for y in range(6):
                print(f"Testing coord: {x},{y}")
                address = self.led_matrix.led_matrix_map[(x, y)]
                self.led_matrix.led_brightness_map[address] = 255
                self.refresh()
                input(f"Is this correct? {address} is what we are turning on. If not you should fix it...")
                self.led_matrix.led_brightness_map[address] = 0
                self.refresh()

    async def display_number(self, number, fade_time=0.5, steps=5):
        if number not in number_patterns:
            print(f"Pattern for number {number} not found.")
            return -1

        pattern = number_patterns[number]
        for step in range(steps + 1):
            brightness = int((math.sin(math.pi * step / steps) ** 2) * 100)
            led_list_x_y = []
            for x in range(self.led_matrix.rows):
                for y in range(self.led_matrix.cols):
                    led_list_x_y.append((x, y, brightness if pattern[x][y] == 1 else 0))
            self.led_matrix.set_led_list(led_list_x_y)
            await asyncio.sleep(fade_time / steps)

    def get_char_pattern(self, char):
        if char.isdigit():
            return number_patterns.get(int(char), [[0]*6]*7)
        elif char.isupper():
            return char_patterns.get(char, [[0]*6]*7)
        elif char in punctuation_patterns:
            return punctuation_patterns[char]
        else:
            return char_patterns_lower.get(char, [[0]*6]*7)

    def scroll_text_frames(self, text="DC32", delay=0.1):
        frames = []

        self.led_matrix.clear_matrix()
        
        # Remove unnecessary leading spaces to prevent buffer overflow
        text = text.lstrip()
        
        # Calculate the necessary buffer size based on text length and matrix dimensions
        buffer_width = max(6 * len(text), self.led_matrix.cols)
        buffer = [[0] * buffer_width for _ in range(self.led_matrix.rows)]

        # Populate the buffer with character patterns
        for i, char in enumerate(text):
            pattern = self.get_char_pattern(char)
            for x in range(self.led_matrix.rows):
                for y in range(6):
                    if i * 6 + y < buffer_width:  # Ensure we do not overflow the buffer
                        buffer[x][i * 6 + y] = pattern[x][y]

        # Create frames for scrolling text
        for offset in range(buffer_width - self.led_matrix.cols + 1):
            led_list = []
            for x in range(self.led_matrix.rows):
                for y in range(self.led_matrix.cols):
                    brightness = 255 if buffer[x][y + offset] == 1 else 0
                    led_list.append((x, y, brightness))
            frames.append((led_list, delay))
        
        return frames

    async def scroll_text(self, text="DC32", delay=0.1):
        frames = self.scroll_text_frames(text, delay)
        self.state_manager.add_frames(frames)
        for frame, frame_delay in frames:
            self.led_matrix.set_led_list(frame)
            await asyncio.sleep(frame_delay)

    def fading_strobe_matrix_frames(self, max_brightness=100, steps=5, fade_delay=10):
        frames = []
        for i in range(steps):
            brightness = int(max_brightness * (i / steps))
            frame = [(x, y, brightness) for x in range(self.led_matrix.rows) for y in range(self.led_matrix.cols)]
            frames.append((frame, fade_delay))
        max_brightness_frame = [(x, y, max_brightness) for x in range(self.led_matrix.rows) for y in range(self.led_matrix.cols)]
        frames.append((max_brightness_frame, 10))
        for i in range(steps, 0, -1):
            brightness = int(max_brightness * (i / steps))
            frame = [(x, y, brightness) for x in range(self.led_matrix.rows) for y in range(self.led_matrix.cols)]
            frames.append((frame, fade_delay))
        frame = [(x, y, 0) for x in range(self.led_matrix.rows) for y in range(self.led_matrix.cols)]
        frames.append((frame, 10))
        return frames

    async def fading_strobe_matrix(self, max_brightness=100, steps=5, fade_delay=10):
        frames = self.fading_strobe_matrix_frames(max_brightness, steps, fade_delay)
        self.state_manager.add_frames(frames)
        for frame, frame_delay in frames:
            self.led_matrix.set_led_list(frame)
            await asyncio.sleep_ms(frame_delay)
