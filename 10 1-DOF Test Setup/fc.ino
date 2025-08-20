#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

RF24 radio(9, 10); // CE, CSN pins
const byte address[6] = "NODE1";

// Helper: convert pin string ("A0", "B1", "C2") → Arduino pin number
int getPinFromName(const char *pinStr) {
  char port = pinStr[0];
  int num = atoi(&pinStr[1]);
  switch (port) {
    case 'A': return PA0 + num;
    case 'B': return PB0 + num;
    case 'C': return PC0 + num;
    default: return -1;
  }
}

// Run one motor pin with PWM value for duration (ms)
void runMotor(int pin, int pwm, unsigned long duration) {
  if (pin < 0) return;
  pinMode(pin, OUTPUT);
  analogWrite(pin, pwm);
  delay(duration);
  analogWrite(pin, 0); // stop
}

void setup() {
  radio.begin();
  radio.openReadingPipe(0, address);
  radio.setPALevel(RF24_PA_LOW);
  radio.startListening();
}

void loop() {
  if (radio.available()) {
    char buffer[32];
    radio.read(&buffer, sizeof(buffer));
    buffer[31] = '\0'; // safety

    // Check command type
    if (strncmp(buffer, "motor1", 6) == 0) {
      // Format: motor1 A0 1200
      char cmd[8], pinStr[4];
      int pwm;
      sscanf(buffer, "%s %s %d", cmd, pinStr, &pwm);
      int pin = getPinFromName(pinStr);
      runMotor(pin, pwm, 5000); // 5s
    }
    else if (strncmp(buffer, "seq", 3) == 0) {
      // Format: seq A0 B1 B2 C1 1200
      char cmd[8], pinStr1[4], pinStr2[4], pinStr3[4], pinStr4[4];
      int pwm;
      sscanf(buffer, "%s %s %s %s %s %d", cmd, pinStr1, pinStr2, pinStr3, pinStr4, &pwm);

      int pins[4] = { getPinFromName(pinStr1), getPinFromName(pinStr2),
                      getPinFromName(pinStr3), getPinFromName(pinStr4) };

      for (int i = 0; i < 4; i++) {
        if (pins[i] >= 0) {
          runMotor(pins[i], pwm, 5000); // 5s
          delay(2000); // 2s gap
        }
      }
    }
  }
}
