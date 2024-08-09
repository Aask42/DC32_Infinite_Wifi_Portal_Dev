#!/bin/bash

# Base directory containing the configuration files
BASE_CONFIG_DIR="/path/to/configs"
# USB port prefix (modify according to your system)
PORT_PREFIX="/dev/ttyUSB"
# Starting index for device configuration
START_INDEX=43
# Ending index for device configuration
END_INDEX=150

# Function to copy files to the MicroPython device
copy_files() {
    local port=$1
    local index=$2
    local config_dir="${BASE_CONFIG_DIR}/device_${index}"
    
    # Check if the configuration directory exists
    if [ -d "$config_dir" ]; then
        echo "Copying files to device at ${port} with config ${config_dir}..."
        # Use the `ampy` or `mpremote` tool to copy files (adjust command as necessary)
        mpremote connect ${port} cp ${config_dir}/* :
        echo "Files copied to device at ${port}."
    else
        echo "Configuration directory for device ${index} not found. Skipping..."
    fi
}

# Main loop to monitor for new devices
while [ $START_INDEX -le $END_INDEX ]; do
    echo "Waiting for device ${START_INDEX} to be plugged in..."
    
    # Wait for a new device to appear
    while [ ! -e "${PORT_PREFIX}${START_INDEX}" ]; do
        sleep 1
    done
    
    # Device found, perform the file copy
    copy_files "${PORT_PREFIX}${START_INDEX}" $START_INDEX
    
    # Increment to the next device index
    START_INDEX=$((START_INDEX + 1))
    
    # Wait for the device to be unplugged before continuing
    echo "Please unplug the device to continue."
    while [ -e "${PORT_PREFIX}${START_INDEX}" ]; do
        sleep 1
    done
done

echo "All devices processed."
