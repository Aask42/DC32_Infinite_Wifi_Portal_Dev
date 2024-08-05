class StateManager:
    def __init__(self):
        self.frames = []
        self.current_frame_index = 0
        self.x_motion = False
        self.y_motion = False
        self.z_motion = False

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

    def set_current_frame(self, frame_num):
        if self.frames:
            self.current_frame_index = frame_num % len(self.frames)
        else:
            self.current_frame_index = 0

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
