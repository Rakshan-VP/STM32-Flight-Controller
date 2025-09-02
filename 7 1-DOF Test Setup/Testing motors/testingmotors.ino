#include <Servo.h>

Servo esc1, esc2, esc3, esc4;   // ESC objects

void setup() {
  // Attach ESCs to pins
  esc1.attach(A0);
  esc2.attach(A1);
  esc3.attach(PB4);
  esc4.attach(PB5);

  // Initialize ESCs with minimum throttle
  esc1.writeMicroseconds(1000);
  esc2.writeMicroseconds(1000);
  esc3.writeMicroseconds(1000);
  esc4.writeMicroseconds(1000);

  delay(3000);   // wait 3s for ESCs to initialize
}

void loop() {
  // Motor 1
  esc1.writeMicroseconds(1300);
  delay(5000);
  esc1.writeMicroseconds(1000);
  delay(2000);

  // Motor 2
  esc2.writeMicroseconds(1300);
  delay(5000);
  esc2.writeMicroseconds(1000);
  delay(2000);

  // Motor 3
  esc3.writeMicroseconds(1300);
  delay(5000);
  esc3.writeMicroseconds(1000);
  delay(2000);

  // Motor 4
  esc4.writeMicroseconds(1300);
  delay(5000);
  esc4.writeMicroseconds(1000);
  delay(2000);
}