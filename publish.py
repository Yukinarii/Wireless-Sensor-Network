import sys
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import json
import Adafruit_DHT
import time
import threading
import Crypto.Cipher import AES

DHT_PIN = 4

# https://www.itread01.com/content/1507657101.html
class prpcrypt():  
    def __init__(self, key):  
        self.key = key  
        self.mode = AES.MODE_CBC  
       
    def encrypt(self, text):  
        cryptor = AES.new(self.key, self.mode, self.key)  
        #這裏密鑰key 長度必須為16（AES-128）、24（AES-192）、或32（AES-256）Bytes 長度.目前AES-128足夠用  
        length = 16  
        count = len(text)  
    if(count % length != 0) :  
            add = length - (count % length)  
    else:  
        add = 0  
        text = text + ('\0' * add)  
        self.ciphertext = cryptor.encrypt(text)  

        return b2a_hex(self.ciphertext)  

    def decrypt(self, text):  
        cryptor = AES.new(self.key, self.mode, self.key)  
        plain_text = cryptor.decrypt(a2b_hex(text))  
        return plain_text.rstrip('\0')

class DHT_fetcher:
    def __init__(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(DHT_PIN, GPIO.IN)
        self.temperature = None
        self.humidity = None
    
    def get_DHT_data(self):
        while True:
            humidity, temperature = Adafruit_DHT.read_retry(
                                              Adafruit_DHT.DHT22, DHT_PIN)
            if humidity is not None and temperature is not None:
                self.humidity = humidity
                self.temperature = temperature
            time.sleep(5)
    
    def start_tmp_thread(self):
        threading.Thread(target = self.get_DHT_data).start()

def main():
    MQTTTopicServerIP = "localhost"
    MQTTTopicServerPort = 1883
    MQTTTopicName = "wsn_lab/test"
    pc = prpcrypt(key = '107062533')
    gpio_setup()
    fetcher = DHT_fetcher()
    fetcher.start_tmp_thread()
    
    Message = ""
    while fetcher.temperature is None:
        continue
    
    Message = Message + str(fetcher.temperature)
    EncryptMessage = pc.encrypt(Message)
    # d = pc.decrypt(EncryptMessage)

    mqttc = mqtt.Client("python_pub")
    mqttc.connect(MQTTTopicServerIP, MQTTTopicServerPort)
    smqttc.publish(MQTTTopicName, EncryptMessage)
