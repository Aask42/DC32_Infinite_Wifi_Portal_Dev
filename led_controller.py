import neopixel
from machine import Pin
from helpers import hsv_to_rgb  # Import the helper function
try:
    from CONFIG.LED_MANAGER import MAX_BRIGHTNESS
except:
    print("You didn't provide a max brightness, setting to 100 to not blind you")
    MAX_BRIGHTNESS = 100
class LEDController:
    def __init__(self, num_pixels, pin_num, brightness, hue_increment, max_color_cycle, max_brightness=MAX_BRIGHTNESS):
        self.num_pixels = num_pixels
        self.np = neopixel.NeoPixel(Pin(pin_num), num_pixels)
        self.brightness = brightness
        self.hue_increment = hue_increment
        self.max_color_cycle = max_color_cycle
        self.max_brightness = max_brightness  # Add max_brightness
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
            color = hsv_to_rgb(current_hue, 1, self.brightness / 255 * self.max_brightness / 255)  # Adjust brightness scale
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

    def set_brightness(self, brightness):
        self.brightness = min(brightness, self.max_brightness)  # Ensure brightness does not exceed max_brightness
