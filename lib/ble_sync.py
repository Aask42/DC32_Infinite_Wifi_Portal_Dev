import uasyncio as asyncio
from machine import Timer, RTC
import time
import ubluetooth
import struct

class BLESync:
    #self.sync_interval_ms = 10000  # Interval to send sync pulses in milliseconds
    RESYNC_THRESHOLD_MS = 50  # Resync if more than 50ms off

    def __init__(self):
        self.ble = ubluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self.ble_irq)
        self.sync_event = asyncio.Event()
        self.sync_timer = Timer(-1)
        self.ble_tick_number = 0
        self.rtc = RTC()
        self.bpm = 0
        self.frame_count = 0
        self.start_scanning()
        self.ble_role = "peripheral"
        self.sync_interval_ms = 10000

    def start_scanning(self):
        print("Starting scan...")
        self.ble.gap_scan(0)  # 0 means no timeout, scans indefinitely

    def ble_irq(self, event, data):
        if event == 1:  # Central connected
            print("Central connected")
        elif event == 2:  # Central disconnected
            print("Central disconnected")
        elif event == 5:  # Scan result
            addr_type, addr, adv_type, rssi, adv_data = data
            adv_data = bytes(adv_data)  # Convert memoryview to bytes
            if adv_data and adv_data.startswith(b'sync_pulse'):
                try:
                    header_len = len(b'sync_pulse')
                    received_time = struct.unpack('>Q', adv_data[header_len:header_len + 8])[0]
                    received_frame = struct.unpack('>Q', adv_data[header_len + 8:header_len + 16])[0]
                    frame_difference = received_frame - self.frame_count
                    current_time = time.ticks_ms()
                    time_diff = abs(time.ticks_diff(current_time, received_time))
                    print(f"Time difference: {time_diff} ms, frame difference: {frame_difference}, current-frame: {self.frame_count}, ble-frame: {received_frame}")
                    
                        
                    if self.ble_role == "peripheral":
                        if time_diff > self.RESYNC_THRESHOLD_MS:
                            self.synced_time = received_time
                            self.sync_event.set()
                        print(f"This is a perhiperal")
                        #self.frame_count += 1
                        self.frame_count = received_frame
                except Exception as e:
                    print(f"Error unpacking data: {e}")

    def send_sync_pulse(self):
        current_time = int(time.time() * 1000)  # Current Unix time in milliseconds
        if self.ble_role == "controller":
            sync_pulse = b'sync_pulse' + struct.pack('>Q', current_time) + struct.pack('>Q', self.frame_count)
        else:
            sync_pulse = b'Hello DEF CON 32!'
        self.ble.gap_advertise(100, sync_pulse)
        print(f"Sent: {sync_pulse}")

    async def sync_clock(self):
        while True:
            await self.sync_event.wait()
            self.sync_event.clear()
            print("Attempting to synchronize clock")
            
            print("Clock synchronized at Unix time (ms):", self.synced_time)
            self.set_system_clock(self.synced_time)

    def set_system_clock(self, unix_time_ms):
        unix_time_s = unix_time_ms // 1000
        tm = time.localtime(unix_time_s)
        milliseconds = unix_time_ms % 1000
        self.rtc.datetime((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], milliseconds * 1000))
        print("System clock set to:", self.rtc.datetime())

    async def periodic_sync(self):
        while True:
           
            self.send_sync_pulse()
            await asyncio.sleep_ms(self.sync_interval_ms)

    async def run(self):
        if self.ble_role == "controller":
            self.sync_interval_ms = 100
        asyncio.create_task(self.periodic_sync())
        await self.sync_clock()

# Start the BLESync
#ble_sync = BLESync()
#ble_sync.ble_role = "peripheral"
#asyncio.run(ble_sync.run())


