"""
Written by: BadAask
Written for: DC32
Date started: 20240720
Copyright: Do what you want because a pirate is free

Description: Basic driver for IS31FL3729 chip
"""

import time

class IS31FL3729:
    
    def __init__(self, i2c, address=0x34, cs_currents = [0x40] * 15, grid_size_mode=[0x61]):
        self.i2c = i2c
        self.address = address
        
        #self.init_display(cs_currents)
        self.led_matrix_map = {}
        self.led_brightness_map = {}
        
        self.cs_currents = cs_currents
        self.grid_size_mode = grid_size_mode
        
        # Initialize the grid dimensions
        self.rows, self.cols = 0, 0


    def i2c_w(self, reg, data):
        buf = bytearray(1)
        buf[0] = reg
        buf.extend(bytearray(data))
        self.i2c.writeto(self.address, buf)

    def start_display(self):
        # Reset all registers
        self.i2c_w(0xcf, [0xae])
        # Set current limit to 16/64
        self.i2c_w(0xa1, [64])
        # Set each current source current
        self.i2c_w(0x90, bytearray(self.cs_currents))
        
        # Enable chip in proper mode, defaults to 3x16 mode
        self.i2c_w(0xa0, self.grid_size_mode)

    def set_led_raw(self, reg, brightness):
        self.i2c_w(reg, [brightness])

    def map_leds(self, num_leds = 45):
        # TODO: Dynamically figure out how many LEDs there are based on the self.grid_size_mode
        leds = [0x00]
        
        for led in num_leds:
            leds.append(led)
            
        for reg in leds:
            self.set_led_raw(reg, 255)  # Turn on the LED
            row = int(input(f"Enter row for LED {hex(reg)}: "))
            col = int(input(f"Enter column for LED {hex(reg)}: "))
            self.led_matrix_map[(row, col)] = reg
            self.set_led_raw(reg, 0)  # Turn off the LED
            time.sleep(0.10)  # Wait a bit before lighting the next LED

        print("Final LED Map:")
        for key, value in sorted(self.led_matrix_map.items()):
            print(f"{key}: {hex(value)}")

    def render_led_map(self):
        led_brightness_list = []
        for i,item in enumerate(self.led_brightness_map):
            brightness_value = self.led_brightness_map[item]
            led_brightness_list.append(brightness_value)
        length_of_list = len(led_brightness_list)
        self.i2c_w(0x00, led_brightness_list)

    
    def set_led(self,reg,brightness):
        self.led_brightness_map[reg] = brightness 
        self.render_led_map()
    
    def set_led_by_coord(self,x,y,brightness):
        reg = hex(self.led_matrix_map[(x,y)])
        
        self.led_brightness_map[reg] = brightness 
        self.render_led_map()
        
    def set_led_list(self,led_list_x_y):
        # led_list_x_y must be a list of all the LEDs you wish to update
        # it should include the x,y coords of the LED you want to update and its brightness
        # like (1,2,100), (1,4,100), etc...
        for x,y,brightness in led_list_x_y:
            reg = self.led_matrix_map[(x,y)]
            #if brightness > 0:
            #    print(f"turning on {reg}: x,y: {x},{y}")
            self.led_brightness_map[reg] = brightness
        self.render_led_map()
        
            
    def clear_matrix(self):
        for led in self.led_brightness_map:
            # skip red and green
            if led == 16 or led == 32:
                #print("Skipping red or green LED")
                continue
            self.led_brightness_map[led] = 0
        self.render_led_map()
 