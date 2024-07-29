import uasyncio as asyncio
from machine import Timer, RTC
import time
import ubluetooth
import struct

class BLESync:
    SYNC_INTERVAL_MS = 10000  # Interval to send sync pulses in milliseconds
    RESYNC_THRESHOLD_MS = 150  # Resync if more than 150ms off
    PRECISION = 1000  # 10th of a millisecond
    CLIENT_TIMEOUT_MS = 20000  # Timeout for clients after hearing a sync from control
    SCAN_INTERVAL_MS = 30000  # Interval to restart scanning in milliseconds

    def __init__(self, role='client'):
        self.role = role
        self.ble = ubluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self.ble_irq)
        self.sync_event = asyncio.Event()
        self.synced_time = None
        self.sync_timer = Timer(-1)
        self.rtc = RTC()
        self.scanning = False
        self.last_sync_from_control = 0

    def ble_irq(self, event, data):
        if event == 1:  # Central connected
            print("Central connected")
        elif event == 2:  # Central disconnected
            print("Central disconnected")
        elif event == 5:  # Scan result
            addr_type, addr, adv_type, rssi, adv_data = data
            adv_data_bytes = bytes(adv_data)  # Convert memoryview to bytes
            #print(f"Advertisement received: {adv_data_bytes}")  # Debugging line
            if adv_data_bytes.startswith(b'sync_pulse') and len(adv_data_bytes) >= 22:
                try:
                    print("Sync pulse detected")
                    received_time_str = adv_data_bytes[12:25].decode()
                    milliseconds = struct.unpack('>H', adv_data_bytes[22:24])[0]
                    print(f"Received time string: {received_time_str}")
                    current_time_ms = time.ticks_ms() + time.ticks_us() % 1000 / 1000
                    self.set_system_clock(received_time_str, milliseconds)
                    if adv_data_bytes[10:12] == b'CT':  # Check if it's from a Control device
                        print("Sync pulse from Control detected")
                        self.last_sync_from_control = time.ticks_ms()
                        self.stop_scan()  # Stop scanning once a sync pulse is received
                except Exception as e:
                    print(f"Error unpacking sync pulse: {e}")

    def start_scan(self):
        if not self.scanning:
            print("Starting BLE scan")
            self.ble.gap_scan(0, 30000, 30000)  # Set scan window and interval to max to continuously scan
            self.scanning = True

    def stop_scan(self):
        if self.scanning:
            print("Stopping BLE scan")
            self.ble.gap_scan(None)  # Stop scanning
            self.scanning = False

    def send_sync_pulse(self):
        current_time = time.localtime()
        current_time_str = f"{current_time[0]:04}{current_time[1]:02}{current_time[2]:02}{current_time[3]:02}{current_time[4]:02}{current_time[5]:02}"
        current_time_ms = int(time.time() * 1000 % 1000)
        role_bytes = b'CT' if self.role == 'control' else b'CL'
        sync_pulse = b'sync_pulse' + role_bytes + current_time_str.encode() + struct.pack('>H', current_time_ms)
        self.ble.gap_advertise(100, sync_pulse, connectable=False)
        print(f"Sent sync pulse: {current_time_str}.{current_time_ms:03d}")

    async def sync_clock(self):
        while True:
            await self.sync_event.wait()
            self.sync_event.clear()
            print("Clock synchronized")

    def set_system_clock(self, time_str, milliseconds):
        try:
            year = int(time_str[0:4])
            month = int(time_str[4:6])
            day = int(time_str[6:8])
            hour = int(time_str[8:10])
            minute = int(time_str[10:12])
            second = int(time_str[12:14])
            #milliseconds = int(time_str[14:16])
            print(f"The new time is: {year}{month}{day} {hour}:{minute}:{second}:{milliseconds}")
        except Exception as e:
            print(f"Go FUCK YOURSELF: {e}")
        self.rtc.datetime((year, month, day, hour, minute, second, milliseconds * 1000, 0))
        print("System clock set to:", self.rtc.datetime())

    async def periodic_sync(self):
        while True:
            if self.role == 'control' or (self.role == 'client' and (time.ticks_diff(time.ticks_ms(), self.last_sync_from_control) > self.CLIENT_TIMEOUT_MS)):
                self.send_sync_pulse()
            await asyncio.sleep_ms(self.SYNC_INTERVAL_MS)
            
    async def periodic_scan(self):
        while True:
            self.start_scan()
            await asyncio.sleep(self.SCAN_INTERVAL_MS / 1000)  # Restart scan at the designated interval
            self.stop_scan()

    async def run(self):
        if self.role == 'client':
            asyncio.create_task(self.periodic_scan())
        
        asyncio.create_task(self.periodic_sync())
        await self.sync_clock()

# Example usage:
# Create a BLESync instance with role 'control' or 'client'
# ble_sync = BLESync(role='control')
# asyncio.run(ble_sync.run())
