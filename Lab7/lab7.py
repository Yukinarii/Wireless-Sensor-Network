from bluepy.btle import UUID, Scanner, DefaultDelegate, Peripheral, Characteristic
import time


class MyDelegate(DefaultDelegate):
    def __init__(self, peripheral):
        DefaultDelegate.__init__(self)
        self.counter = 0
        self.peripheral = peripheral
        self.SYN = False
        self.ACK = False

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            print("Discovered device %s" %(dev.addr))
    
    def handleNotification(self, hdl, data):
        if self.SYN is False:# and data.decode('ascii') is "SYN":
            self.SYN = True
            message = "SYN_ACK"
            print("received SYN")
            message = message.encode('ascii')
            self.peripheral.writeCharacteristic(hdl, message, True)
        elif self.SYN is True:
            if self.ACK is False:
                self.ACK = True
                message = "handshaking completed"
                print("received ACK")
                message = message.encode('ascii')
                self.peripheral.writeCharacteristic(hdl, message, True)
            elif self.ACK is True:
                print("Received message: " + data.decode('ascii'))
                message = input('>>')
                message = message.encode('ascii')
                self.peripheral.writeCharacteristic(hdl, message, True)
        else:
            print(data.decode('ascii'))


hc08 = Peripheral() 
hc08.connect("a8:e2:c1:62:7f:bc", "public")

hc08.withDelegate(MyDelegate(hc08))

while True:
    print("Start waiting for messages...")
    hc08.waitForNotifications(10.0)
