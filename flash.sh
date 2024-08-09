#!/bin/bash

# Define the port and the esptool.py commands
PORT="/dev/tty.usbserial-110"
ERASE_CMD="/Users/ameliawietting/.espressif/python_env/idf5.0_py3.12_env/bin/python ../../../../esp-idf/components/esptool_py/esptool/esptool.py -p $PORT -b 460800 erase_flash"
FLASH_CMD="/Users/ameliawietting/.espressif/python_env/idf5.0_py3.12_env/bin/python ../../../../esp-idf/components/esptool_py/esptool/esptool.py -p $PORT -b 460800 --before default_reset --after hard_reset --chip esp32 write_flash --flash_mode dio --flash_size 4MB --flash_freq 40m 0x1000 build-ESP32_GENERIC/bootloader/bootloader.bin 0x8000 build-ESP32_GENERIC/partition_table/partition-table.bin 0x10000 build-ESP32_GENERIC/micropython.bin"

# Function to check if the port is connected
is_port_connected() {
    ls $PORT &> /dev/null
    return $?
}

# Main loop to monitor port connection status
while true; do
    if ! is_port_connected; then
        echo "Port $PORT disconnected. Waiting for reconnection..."
        while ! is_port_connected; do
            sleep 1
        done
        echo "Port $PORT reconnected. Running esptool.py commands..."

        # Run the erase flash command
        echo "Running erase_flash..."
        $ERASE_CMD
        if [ $? -ne 0 ]; then
            echo "Erase flash command failed."
            continue
        fi

        # Run the write flash command
        echo "Running write_flash..."
        $FLASH_CMD
        if [ $? -ne 0 ]; then
            echo "Write flash command failed."
            continue
        fi

        echo "Commands executed successfully."
    fi
    sleep 1
done

