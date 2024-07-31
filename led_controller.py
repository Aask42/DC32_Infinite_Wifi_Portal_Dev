import neopixel
from machine import Pin
from helpers import hsv_to_rgb  # Import the helper function

class LEDController:
    def __init__(self, num_pixels, pin_num, brightness, hue_increment, max_color_cycle):
        self.num_pixels = num_pixels
        self.np = neopixel.NeoPixel(Pin(pin_num), num_pixels)
        self.brightness = brightness
        self.hue_increment = hue_increment
        self.max_color_cycle = max_color_cycle
        self.position = 0
        self.cycle = 0
        self.direction = 1
        self.frame_count = 0

    def update_direction(self):
        self.direction *= -1  # Change direction properly

    def update_position(self):
        self.position = (self.position + self.direction) % self.num_pixels

    def generate_frame(self):
        frame = [(0, 0, 0)] * self.num_pixels
        base_hue = (self.cycle / self.max_color_cycle) % 1
        for offset in range(5):
            current_hue = (base_hue + offset * self.hue_increment) % 1
            color = hsv_to_rgb(current_hue, 1, self.brightness)
            idx = (self.position + offset) % self.num_pixels
            frame[idx] = color
        return frame
    
    def display_frame(self, frame):
        self.np.fill((0, 0, 0))
        for idx, color in enumerate(frame):
            self.np[idx] = color
        self.np.write()
        self.frame_count += 1

    def update_strip(self, t):
        frame = self.generate_frame()
        self.display_frame(frame)
        self.update_position()
        self.cycle = (self.cycle + self.direction) % self.max_color_cycle
        if self.cycle < 0:
            self.cycle = self.max_color_cycle - 1

