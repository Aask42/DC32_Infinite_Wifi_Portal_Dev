import uos
import gc
import micropython as mp
import urequests
import uasyncio as asyncio
from CONFIG.OTA_CONFIG import OTA_HOST, PROJECT_NAME, FILENAMES
from CONFIG.MQTT_CONFIG import MQTT_CLIENT_ID

class OTAUpdater:
    def __init__(self, msg_string: str):
        self.msg_string = msg_string
    
    async def update_file_replace(self):
        """
        Updates a file from an OTA server.
        
        This method fetches the file content from the OTA server and replaces
        the local file with the new content.

        :raises Exception: If there's an error during the update process.
        """
        print(f"Starting update process for {self.msg_string}...")
        filename = self.msg_string
        
        mp.mem_info(1)
        gc.collect()
        
        try:
            updated = False
            print(f"Updating file {filename}")
            
            for i, item in enumerate(FILENAMES):
                print(f"Seeing if {filename} is in {item}")

                if filename in item:
                    file_to_write = item
                    print(f"Found filename! Simple name: {filename} Fully Qualified: {item}")
                    
                    # Clean up and create tmp directory
                    try:
                        uos.mkdir('tmp')
                    except:
                        pass

                    updated = False
                    file_to_write = FILENAMES[i]
                    
                    response_text = await self._http_get(f'{OTA_HOST}/ota_updates/{MQTT_CLIENT_ID}/{filename}')

                    print(f"Response text received: {response_text}")

                    print(f"Going to try to write to tmp/{filename}")

                    with open(f'tmp/{filename}', 'w') as source_file:
                        source_file.write(response_text)

                    # Overwrite our onboard file               
                    with open(f'tmp/{filename}', 'r') as source_file, open(file_to_write, 'w') as target_file:
                        target_file.write(source_file.read())

                    uos.remove(f'tmp/{filename}')
                    
                    try:
                        uos.rmdir('tmp')
                    except:
                        pass
                    break

        except Exception as e:
            print(f"Exception updating file! {e}")

    async def _http_get(self, url: str) -> str:
        """
        Perform a non-blocking HTTP GET request to the specified URL.

        :param url: The URL to fetch.
        :return: The response text.
        """
        try:
            response = urequests.get(url)
            response_text = response.text
            response.close()
            return response_text
        except Exception as e:
            print(f"Exception during HTTP GET: {e}")
            return ""
