#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

RF24 radio(6, 7); // CE, CSN pins
const byte address[6] = "NODE1";

void setup() {
  Serial.begin(9600);
  radio.begin();
  radio.openWritingPipe(address);
  radio.setPALevel(RF24_PA_LOW);
  radio.stopListening();
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd.length() > 0) {
      char buffer[32];
      cmd.toCharArray(buffer, sizeof(buffer));
      radio.write(&buffer, sizeof(buffer));
      Serial.print("Sent: ");
      Serial.println(cmd);
    }
  }
}
