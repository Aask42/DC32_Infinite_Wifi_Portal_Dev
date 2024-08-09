#!/usr/bin/python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import threading
from socketserver import ThreadingMixIn

hostName = "0.0.0.0"
serverPort = 8000

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Extract the MQTT ID and file name from the URL path
        path_parts = self.path.strip("/").split("/")
        print(f"{path_parts}")
        if len(path_parts) >= 2:
            mqtt_id = path_parts[1]
            filename = path_parts[-1]
            print(f"{mqtt_id}, {filename}")
        else:
            self.send_error(404, "If you're looking for Aask https://aask.ltd")
            return

        # Mapping of filenames to their respective paths
        # Mapping of filenames to their respective paths
        file_map = {
            "main.py": f"./ota_updates/main.py",   
            "IS31FL3729.py": f"./ota_updates/IS31FL3729.py",   
            "LIS2DW12.py": f"./ota_updates/lib/LIS2DW12.py",   
            "LTR_308ALS.py": f"./ota_updates/lib/LTR_308ALS.py",   
            "simple.py": f"./ota_updates/lib/umqtt/simple.py",   
            "animations.py": f"./ota_updates/src/animations.py",
            "ble_sync.py": f"./ota_updates/src/ble_sync.py",
            "helpers.py": f"./ota_updates/src/helpers.py",
            "led_controller.py": f"./ota_updates/src/led_controller.py",
            "light_sensor_manager.py": f"./ota_updates/src/light_sensor_manager.py",
            "motion_sensor.py": f"./ota_updates/src/motion_sensor.py",
            "light_sensor_manager.py": f"./ota_updates/src/light_sensor_manager.py",
            "mqtt_manager.py": f"./ota_updates/src/mqtt_manager.py",
            "state_manager.py": f"./ota_updates/src/state_manager.py",
            "updates.py": f"./ota_updates/src/updates.py",
            "infinity_mirror_font.py": f"./ota_updates/src/matrix_functions/infinity_mirror_font.py",
            "matrix_manager.py": f"./ota_updates/src/matrix_functions/matrix_manager.py",
            "matrix_setup.py": f"./ota_updates/src/matrix_functions/matrix_setup.py",
            "wifi_manager.py": f"./ota_updates/src/wifi_manager.py",
            "conways_game.py": f"./ota_updates/examples/conways_game.py",
            "scroll_name.py": f"./ota_updates/examples/scroll_name.py",
            "test_led_render.py": f"./ota_updates/examples/test_led_render.py",
            "BLE_CONFIG.py": f"./ota_updates/{mqtt_id}/CONFIG/BLE_CONFIG.py",  
            "WIFI_CONFIG.py": f"./ota_updates/{mqtt_id}/CONFIG/WIFI_CONFIG.py",  
            "MQTT_CONFIG.py": f"./ota_updates/{mqtt_id}/CONFIG/MQTT_CONFIG.py",   
            "CLOCK_CONFIG.py": f"./ota_updates/{mqtt_id}/CONFIG/CLOCK_CONFIG.py",   
            "LED_MANAGER.py": f"./ota_updates/{mqtt_id}/CONFIG/LED_MANAGER.py",   
            "OTA_CONFIG.py": f"./ota_updates/{mqtt_id}/CONFIG/OTA_CONFIG.py",
        }


        if filename in file_map:
            file_path = file_map[filename]
            # Check if the file exists
            if os.path.isfile(file_path):
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                with open(file_path, 'rb') as file:
                    self.wfile.write(file.read())
            else:
                self.send_error(404, "Couldn't find file, maybe you're looking for Aask https://aask.ltd")
        else:
            self.send_error(404, "File not in file map...If you're looking for Aask https://aask.ltd")


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

if __name__ == "__main__":
    webServer = ThreadedHTTPServer((hostName, serverPort), Handler)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
