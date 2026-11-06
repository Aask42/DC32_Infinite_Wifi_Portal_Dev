import uhashlib
import gc

class StateManager:
    def __init__(self):
        self.current_frame_index = 0
        self.frame_index_to_hash = []
        self.frame_hash_table = {}
        self.x_motion = False
        self.y_motion = False
        self.z_motion = False
        self.fading_up = False
        self.fading_down = False
        self.brightness_step = 50  # Default starting brightness
        self.brightness_target = 100  # Default target brightness
        self.matrix_brightness = 100
        self.lux_modifier = 1.0  # Default lux modifier
        self._adds_since_gc = 0
    
    def set_brightness_led_matrix(self, matrix_brightness=100):
        self.matrix_brightness = matrix_brightness
    
    def get_brightness_led_matrix(self):
        return self.matrix_brightness

    def set_lux_modifier(self, lux_value):
        self.lux_modifier = max(0.0, min(1.0, lux_value / 1000.0))  # Normalize lux value to a range [0, 1]

    def get_lux_modifier(self):
        return self.lux_modifier

    def add_frame(self, frame, delay):
        frame_hash = self._hash_frame(frame)
        if frame_hash not in self.frame_hash_table:
            self.frame_hash_table[frame_hash] = frame
        self.frame_index_to_hash.append((frame_hash, delay))
        # This used to gc.collect() on EVERY frame. Loading a few hundred
        # frames (scroll text, pre-calculated Conway) made startup crawl
        # through hundreds of full heap collections. Collect in batches.
        self._adds_since_gc += 1
        if self._adds_since_gc >= 32:
            self._adds_since_gc = 0
            gc.collect()

    def get_current_frame(self):
        if self.frame_index_to_hash:
            if self.current_frame_index >= len(self.frame_index_to_hash):
                self.current_frame_index = 0
            frame_hash, delay = self.frame_index_to_hash[self.current_frame_index]
            frame = self.frame_hash_table[frame_hash]
            self.current_frame_index = (self.current_frame_index + 1) % len(self.frame_index_to_hash)
            return frame, delay
        return None, 0

    def set_current_frame(self, frame_num):
        if self.frame_index_to_hash:
            self.current_frame_index = frame_num % len(self.frame_index_to_hash)
        else:
            self.current_frame_index = 0

    def num_frames(self):
        return len(self.frame_index_to_hash)

    def get_synced_frame(self, clock, pingpong=False):
        """Return the frame for right now according to a shared FrameClock
        (see src/time_sync.py), instead of the free-running counter.

        Every badge with an NTP-synced clock computes the same index, so
        all badges show the same frame at the same moment and drift can
        never accumulate. Falls back to (None, 0) when no frames are
        loaded, exactly like get_current_frame()."""
        count = len(self.frame_index_to_hash)
        if not count:
            return None, 0
        self.current_frame_index = clock.index_at(count, pingpong=pingpong)
        return self.get_current_frame()

    def update_motion_state(self, motion_sensor):
        self.x_motion = motion_sensor.x_motion
        self.y_motion = motion_sensor.y_motion
        self.z_motion = motion_sensor.z_motion

    def print_motion_state(self):
        if self.x_motion:
            print("X motion detected")
            self.x_motion = False
        if self.y_motion:
            print("Y motion detected")
            self.y_motion = False
        if self.z_motion:
            print("Z motion detected")
            self.z_motion = False

    def _hash_frame(self, frame):
        # Packed frames are already ints, and an int is its own perfect
        # dictionary key. The old code SHA256-hashed every frame anyway,
        # which allocated a bytes object per unique frame and burned CPU
        # on every add_frame() for zero benefit -- two different frames
        # can never collide when the key IS the frame. The digest path is
        # kept for any non-int frame a caller might still pass.
        if isinstance(frame, int):
            return frame
        frame_bytes = frame.to_bytes(8, 'big')  # Ensure frame is treated as an integer
        return uhashlib.sha256(frame_bytes).digest()[:8]  # 64-bit hash

    def _convert_64bit_to_frame(self, frame_int):
        frame = []
        for x in range(7):
            for y in range(6):
                bit_index = x * 6 + y
                brightness = 255 if (frame_int & (1 << bit_index)) else 0
                frame.append((x, y, brightness))
        return frame