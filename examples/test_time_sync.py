import utime
import ntptime


ntptime.host = NTP_SERVER
NTP_SERVER="time-a-g.nist.gov"
ntptime.settime()

while True:
    bpm = 60
    tick_interval = bpm/60
    time_ms = (utime.time_ns()/1000)
    while time_ms % tick_interval != 0:
        time.sleep_ms(1)        
    print(f"The current time is synced to {time_ms}")