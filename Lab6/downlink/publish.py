import sys
import paho.mqtt.client as mqtt
import time
import threading
from Crypto.Cipher import AES
import base64


# https://www.itread01.com/content/1547711886.html
class prpcrypt():  
    def __init__(self, key):  
        self.key = key  
        self.mode = AES.MODE_CBC  
    
    def encrypt(self, text):  
        iv = '0102030405060708'
        pad = lambda s: s + (16 - len(s)%16) * chr(16 - len(s)%16)
        text = pad(text)
        
        cipher = AES.new(self.key.encode('utf8'), self.mode, iv.encode('utf8'))
        encryptedbytes = cipher.encrypt(text.encode('utf8'))

        encodestrs = base64.b64encode(encryptedbytes)
        enctext = encodestrs.decode('utf8')
        return enctext

    def decrypt(self, text):  
        iv = '0102030405060708'
        text = text.encode('utf8')
        encodebytes = base64.decodebytes(text)

        cipher = AES.new(self.key.encode('utf8'), self.mode, iv.encode('utf8'))
        text_decrypted = cipher.decrypt(encodebytes)
        unpad = lambda s: s[0:-s[-1]]
        text_decrypted = unpad(text_decrypted)
        text_decrypted = text_decrypted.decode('utf8')
        return text_decrypted


def main():
    MQTTTopicServerIP = "192.168.137.219"
    MQTTTopicServerPort = 1883
    MQTTTopicName = "wsn_lab/test"
    pc = prpcrypt(key = '0000000107062533')

    Message = input('>>')

    EncryptMessage = pc.encrypt(str(Message))
    # d = pc.decrypt(EncryptMessage)

    mqttc = mqtt.Client("python_pub")
    mqttc.connect(MQTTTopicServerIP, MQTTTopicServerPort)
    print(EncryptMessage)
    mqttc.publish(MQTTTopicName, EncryptMessage)

if __name__ == '__main__': main()
