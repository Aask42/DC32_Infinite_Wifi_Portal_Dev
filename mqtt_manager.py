from umqtt.simple import MQTTClient
import uasyncio

class MQTTManager:
    def __init__(self, server, client_id, username=None, password=None):
        self.server = server
        self.client_id = client_id
        self.username = username
        self.password = password
        self.client = MQTTClient(
            client_id=self.client_id,
            server=self.server,
            user=self.username,
            password=self.password
        )
        self.mqtt_connected = False

    def set_callback(self, callback):
        self.client.set_callback(callback)

    def connect(self):
        try:
            self.client.connect()
            self.mqtt_connected = True
            print(f'Connected to {self.server} MQTT broker')
        except Exception as e:
            print(f'Error connecting to {self.server} MQTT broker: {e}')
            self.mqtt_connected = False

    def subscribe(self, topic):
        if self.mqtt_connected:
            try:
                self.client.subscribe(topic)
                print(f'Subscribed to {topic} topic')
            except Exception as e:
                print(f'Error subscribing to {topic} topic: {e}')

    def publish(self, topic, message):
        if self.mqtt_connected:
            try:
                self.client.publish(topic, message)
                print(f'Published message to {topic} topic: {message}')
            except Exception as e:
                print(f'Error publishing to {topic} topic: {e}')

    async def check_messages(self):
        while True:
            try:
                self.client.check_msg()
                await uasyncio.sleep(0.5)
            except Exception as e:
                print(f'Error checking messages: {e}')


