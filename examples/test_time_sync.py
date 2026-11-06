"""
Time sync check for the Infinite Wifi Portal.

The old version of this example could not run: it used NTP_SERVER before
defining it, called time.sleep_ms without importing time, and busy-waited
on a float modulo. This version uses src/time_sync.py, the same code
main.py syncs animations with.

Run it on two badges side by side (WiFi must be connected first -- this
example assumes the network is already up, e.g. via
src/wifi_manager.py). Both badges should print the SAME step, and flip
to the next step at the same moment, because the step is computed from
NTP time rather than counted locally.
"""

import time
from src.time_sync import TimeSync, FrameClock

time_sync = TimeSync()
time_sync.sync()  # prints a message and returns False instead of raising if NTP is unreachable

clock = FrameClock(time_sync, frame_ms=1000)  # 1 frame per second, like Conway

while True:
    now = time_sync.now_ms()
    print("now_ms: {}  step: {}  index of 10 frames: {}  pingpong: {}".format(
        now,
        clock.step_at(now),
        clock.index_at(10, now),
        clock.index_at(10, now, pingpong=True)))
    time.sleep(1)
