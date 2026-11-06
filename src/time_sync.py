"""
Written for: DC32 Infinite Wifi Portal
Description: Shared absolute-time base for multi-badge synchronization.

Why this exists:
    The old sync options both let badges drift apart. MQTT 'bpm' messages
    reset every badge's frame counter to 0, but between messages each
    badge free-runs on its own hardware timer, and BLE sync broadcast a
    frame counter that nothing ever listened to.

    This module takes the opposite approach: if every badge's clock is
    set from the same NTP server, every badge can compute the SAME frame
    index from wall-clock time alone:

        step = (now_ms - epoch_ms) // frame_ms

    There is no leader and no per-frame traffic. A badge that falls
    behind (or boots late, or misses messages) snaps to the correct
    frame on its next display tick instead of chasing it, and error
    cannot accumulate -- the only residual offset is NTP error (a few
    tens of ms on a LAN) plus RTC drift between periodic re-syncs.

    epoch_ms defaults to 0 (the Unix epoch), so all badges agree on the
    timeline with zero configuration and zero communication.

Usage (see main.py):
    time_sync = TimeSync()
    if wifi_manager.wifi_connected:
        time_sync.sync()
    if time_sync.synced:
        frame_clock = FrameClock(time_sync, frame_ms=1000)
        index = frame_clock.index_at(num_frames, pingpong=True)
"""

import time
import ntptime
import gc

DEFAULT_NTP_HOST = "pool.ntp.org"
DEFAULT_RESYNC_S = 3600  # Re-sync NTP hourly; ESP32 RTC drift stays << 1 frame.


class TimeSync:
    """NTP-synced clock with millisecond resolution between syncs.

    time.time() on the RTC only has 1-second resolution, so after each
    NTP sync we anchor the free-running ticks_ms() counter to the RTC's
    next whole-second boundary. now_ms() then extrapolates from that
    anchor: sub-second phase is accurate to a few ms on every badge,
    which is what makes frame boundaries line up across badges.
    """

    def __init__(self, ntp_host=DEFAULT_NTP_HOST, resync_s=DEFAULT_RESYNC_S):
        self.ntp_host = ntp_host
        self.resync_s = resync_s
        self.synced = False
        self._anchor_epoch_ms = 0
        self._anchor_ticks_ms = 0
        self._last_attempt_ticks_ms = None

    def sync(self):
        """Set the RTC from NTP and re-anchor. Returns True on success,
        False (with a printed reason) instead of raising, so a badge with
        no reachable NTP server still runs -- it just free-runs."""
        try:
            ntptime.host = self.ntp_host
            ntptime.settime()
            # Pair the RTC's next second rollover with ticks_ms().
            second = time.time()
            while time.time() == second:
                time.sleep_ms(1)
            self._anchor_ticks_ms = time.ticks_ms()
            self._anchor_epoch_ms = (second + 1) * 1000
            self.synced = True
            print("Time synced via NTP ({}); epoch anchor {} ms".format(
                self.ntp_host, self._anchor_epoch_ms))
        except Exception as e:
            self.synced = False
            print("NTP sync failed ({}); clock not synced".format(e))
        self._last_attempt_ticks_ms = time.ticks_ms()
        gc.collect()
        return self.synced

    def now_ms(self):
        """Milliseconds since the Unix epoch (UTC)."""
        if not self.synced:
            return time.time() * 1000
        return self._anchor_epoch_ms + time.ticks_diff(
            time.ticks_ms(), self._anchor_ticks_ms)

    def maybe_resync(self):
        """Call from the main loop (about once a second). Re-syncs at
        most once per resync_s interval, including retrying after a
        failed initial sync. Returns True if a sync just succeeded."""
        now = time.ticks_ms()
        if self._last_attempt_ticks_ms is not None:
            if time.ticks_diff(now, self._last_attempt_ticks_ms) < self.resync_s * 1000:
                return False
        return self.sync()


class FrameClock:
    """Maps absolute time to an animation frame index.

    All badges sharing an NTP server, a frame_ms and an epoch_ms compute
    the same index at the same moment -- that is the whole sync protocol.
    """

    def __init__(self, time_sync, frame_ms=1000, epoch_ms=0):
        self.time_sync = time_sync
        self.frame_ms = max(1, int(frame_ms))
        self.epoch_ms = epoch_ms

    def set_frame_ms(self, frame_ms):
        self.frame_ms = max(1, int(frame_ms))

    def set_bpm(self, bpm, frames_per_beat=4):
        """Match the tempo of an MQTT 'bpm' message. main.py's display
        timer runs at bpm/4 Hz (4 frames per beat), so a beat is split
        into frames_per_beat equal steps."""
        if bpm and bpm > 0:
            self.frame_ms = max(1, int(60000 / (bpm * frames_per_beat)))

    def step_at(self, now_ms=None):
        """Ever-increasing step counter for the given time (default: now)."""
        if now_ms is None:
            now_ms = self.time_sync.now_ms()
        return (now_ms - self.epoch_ms) // self.frame_ms

    def index_at(self, num_frames, now_ms=None, pingpong=False):
        """Frame index to display at the given time (default: now).

        pingpong=True plays the sequence forwards then backwards
        (0..n-1..1, 0, ...) from the same shared step counter, so synced
        badges turn around at the same moment too."""
        if num_frames <= 0:
            return 0
        step = self.step_at(now_ms)
        if not pingpong:
            return step % num_frames
        if num_frames == 1:
            return 0
        cycle = 2 * (num_frames - 1)
        pos = step % cycle
        return pos if pos < num_frames else cycle - pos
