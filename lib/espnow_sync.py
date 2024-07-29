import uasyncio as asyncio
from machine import Timer, RTC
import time
import struct
import espnow
import network

class ESPNOWSync:
    SYNC_INTERVAL_MS = 1000  # Interval to send sync pulses in milliseconds
    RESYNC_THRESHOLD_MS = 50  # Resync if more than 50ms off
    PRECISION = 100  # 10th of a millisecond

    def __init__(self):
        self.espnow = espnow.ESPNow()
        self.espnow.init()
        self.espnow.on_recv(self.on_recv)
        self.sync_event = asyncio.Event()
        self.synced_time = None
        self.sync_timer = Timer(-1)
        self.rtc = RTC()
        self.peer = None

    def on_recv(self, mac, msg):
        if msg.startswith(b'sync_pulse'):
            print("Sync pulse received")
            received_time = struct.unpack('>QH', msg[10:20])  # Unpack Unix time in milliseconds and 10ths of ms
            received_time_ms = received_time[0] + received_time[1] / 1000
            current_time_ms = time.ticks_ms() + time.ticks_us() % 1000 / 1000
            time_diff = abs(current_time_ms - received_time_ms)
            if time_diff > self.RESYNC_THRESHOLD_MS / 1000:
                self.synced_time = received_time_ms
                self.sync_event.set()

    def send_sync_pulse(self):
        current_time_ms = int(time.time() * 1000)
        current_time_10th_ms = int((time.time() * 1000 % 1) * 1000)
        sync_pulse = b'sync_pulse' + struct.pack('>QH', current_time_ms, current_time_10th_ms)
        if self.peer:
            self.espnow.send(self.peer, sync_pulse)
        print(f"Sent sync pulse: {current_time_ms}.{current_time_10th_ms:03d} ms")

    async def sync_clock(self):
        while True:
            await self.sync_event.wait()
            self.sync_event.clear()
            print("Clock synchronized at Unix time (ms):", self.synced_time)
            self.set_system_clock(self.synced_time)

    def set_system_clock(self, unix_time_ms):
        unix_time_s = int(unix_time_ms // 1000)
        milliseconds = int(unix_time_ms % 1000)
        tenths_ms = int((unix_time_ms % 1) * 1000)
        tm = time.localtime(unix_time_s)
        self.rtc.datetime((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], milliseconds * 1000 + tenths_ms * 100))
        print("System clock set to:", self.rtc.datetime())

    async def periodic_sync(self):
        while True:
            self.send_sync_pulse()
            await asyncio.sleep_ms(self.SYNC_INTERVAL_MS)

    def add_peer(self, peer_mac):
        self.peer = peer_mac
        self.espnow.add_peer(peer_mac)

    async def run(self):
        asyncio.create_task(self.periodic_sync())
        await self.sync_clock()
