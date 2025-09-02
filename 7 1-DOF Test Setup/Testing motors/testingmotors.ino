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
  // Run all motors at 1300 PWM
  esc1.writeMicroseconds(1300);
  esc2.writeMicroseconds(1300);
  esc3.writeMicroseconds(1300);
  esc4.writeMicroseconds(1300);

  delay(5000);   // run for 5 seconds

  // Stop all motors (minimum throttle)
  esc1.writeMicroseconds(1000);
  esc2.writeMicroseconds(1000);
  esc3.writeMicroseconds(1000);
  esc4.writeMicroseconds(1000);

  delay(2000);   // wait for 2 seconds
}
