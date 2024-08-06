"""
Written by: Amelia Wietting
Date: 20240730
For: DEF CON 32
Description: WiFi Connection Library for DC32 Infinite Wifi Portal
"""

from CONFIG.WIFI_CONFIG import WIFI_LIST, MAX_WIFI_CONNECT_TIMEOUT
import network
import uasyncio as asyncio
import gc

class WiFiConnection:
    def __init__(self):
        self.wifi_connected = False
        self.wlan = network.WLAN(network.STA_IF)

    def start_wifi_card(self):
        self.wlan.active(True)
        print("WiFi card initialized")

    async def connect_to_wifi(self):
        self.wifi_connected = False
        connection_attempts = 0

        try:
            nets = self.wlan.scan()
            print(nets)
            for net in nets:
                for network_config in WIFI_LIST:
                    ssid_to_find = network_config[0]
                    if ssid_to_find == net[0].decode('utf-8'):
                        print(f'Attempting to connect to SSID: {ssid_to_find}')
                        if len(network_config) == 1:
                            self.wlan.connect(ssid_to_find)
                        else:
                            self.wlan.connect(ssid_to_find, network_config[1])
                      
                        while not self.wlan.isconnected():
                            connection_attempts += 1
                            await asyncio.sleep(1)
                            if connection_attempts > MAX_WIFI_CONNECT_TIMEOUT:
                                print("Exceeded MAX_WIFI_CONNECT_TIMEOUT!")
                                break
                        
                        if self.wlan.isconnected():
                            self.wifi_connected = True
                            print('WLAN connection succeeded!')
                            break
                if self.wifi_connected:
                    break
        except Exception as e:
            print(f"Setup failed: {e}")

    async def setup_wireless(self):
        self.start_wifi_card()
        await self.connect_to_wifi()
        if not self.wifi_connected:
            print('Failed to connect to WiFi')
        else:
            print('WiFi connected successfully')

    async def check_connections(self):
        while True:
            if not self.wlan.isconnected():
                print('WiFi disconnected, attempting to reconnect...')
                self.wlan.active(False)  # Deactivate the WiFi interface
                await asyncio.sleep(1)  # Wait a bit before reinitializing
                self.start_wifi_card()  # Reactivate the WiFi interface
                await asyncio.sleep(1)  # Wait a bit before reinitializing

                await self.connect_to_wifi()  # Attempt to reconnect
                gc.collect()
            await asyncio.sleep(10)

    async def main(self):
        await self.setup_wireless()
        asyncio.create_task(self.check_connections())
