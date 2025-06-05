#include <SPI.h>
#include <RF24.h>

#define CE_PIN 6
#define CSN_PIN 7

RF24 radio(CE_PIN, CSN_PIN);
const uint64_t address = 0xF0F0F0F0E1LL;

struct RPY {
  float roll;
  float pitch;
  float yaw;
};

void setup() {
  Serial.begin(115200);
  radio.begin();
  radio.openReadingPipe(0, address);
  radio.setPALevel(RF24_PA_LOW);
  radio.startListening();

  Serial.println("Receiver ready");
}

void loop() {
  if (radio.available()) {
    RPY rpy;
    radio.read(&rpy, sizeof(rpy));
    Serial.print("Received -> Roll: ");
    Serial.print(rpy.roll);
    Serial.print(", Pitch: ");
    Serial.print(rpy.pitch);
    Serial.print(", Yaw: ");
    Serial.println(rpy.yaw);
  }
}
