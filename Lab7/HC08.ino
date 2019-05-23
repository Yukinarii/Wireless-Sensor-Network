#include <SoftwareSerial.h>

SoftwareSerial BTSerial(8, 9); // RX | TX

void setup()
{
  Serial.begin(9600);
  Serial.println("Enter AT commands:");
  BTSerial.begin(9600);  // HC-08 default speed in AT command mode
}

void loop()
{
  // Keep reading from HC-08 and send to Arduino Serial Monitor
  char c;
  BTSerial.write("AT");
  if (BTSerial.available()){
    c = BTSerial.read();
    Serial.print(c);
  }

  // Keep reading from Arduino Serial Monitor and send to HC-08
  if (Serial.available()){
    BTSerial.write(Serial.read());
  }
}
