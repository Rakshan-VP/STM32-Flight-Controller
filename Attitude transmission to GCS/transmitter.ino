#include <Wire.h>
#include <MPU6050.h>         
#include <RF24.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_HMC5883_U.h> 
// NRF24L01 pins on Black Pill
#define CE_PIN PB0
#define CSN_PIN PA4

RF24 radio(CE_PIN, CSN_PIN);
const uint64_t address = 0xF0F0F0F0E1LL;

MPU6050 mpu;
Adafruit_HMC5883_Unified mag = Adafruit_HMC5883_Unified(12345);

struct RPY {
  float roll;
  float pitch;
  float yaw;
};

void setup() {
  Serial.begin(115200);
  Wire.begin();

  // Initialize MPU6050
  mpu.initialize();
  if (!mpu.testConnection()) {
    Serial.println("MPU6050 connection failed");
    while (1);
  }
  Serial.println("MPU6050 initialized");

  // Initialize Magnetometer
  if (!mag.begin()) {
    Serial.println("HMC5883 not detected");
    while (1);
  }
  Serial.println("HMC5883 initialized");

  radio.begin();
  radio.openWritingPipe(address);
  radio.setPALevel(RF24_PA_LOW);
  radio.stopListening();

  Serial.println("Setup complete");
}

RPY computeRPY() {
  int16_t ax, ay, az;
  mpu.getAcceleration(&ax, &ay, &az);

  float axf = ax / 16384.0;
  float ayf = ay / 16384.0;
  float azf = az / 16384.0;

  // Axis mapping
  float x_acc = -ayf; // mpu's -y
  float y_acc = axf;  // mpu's x
  float z_acc = azf;  // unchanged

  float roll = atan2(y_acc, z_acc);
  float pitch = atan2(-x_acc, sqrt(y_acc * y_acc + z_acc * z_acc));

  // Negate pitch as you requested
  pitch = -pitch;

  sensors_event_t event;
  mag.getEvent(&event);

  float mag_x = -event.magnetic.x;  // mag's -x
  float mag_y = -event.magnetic.y;  // mag's -y
  float mag_z = event.magnetic.z;

  // Tilt compensation
  float mag_x_comp = mag_x * cos(pitch) + mag_y * sin(roll) * sin(pitch) + mag_z * cos(roll) * sin(pitch);
  float mag_y_comp = mag_y * cos(roll) - mag_z * sin(roll);

  float yaw = atan2(-mag_y_comp, mag_x_comp);

  // Convert to degrees
  roll = roll * 180.0 / PI;
  pitch = pitch * 180.0 / PI;
  yaw = yaw * 180.0 / PI;

  // Wrap yaw to [-180,180]
  if (yaw > 180) yaw -= 360;
  else if (yaw < -180) yaw += 360;

  return {roll, pitch, yaw};
}


void loop() {
  RPY rpy = computeRPY();

  Serial.print("Roll: "); Serial.print(rpy.roll);
  Serial.print(", Pitch: "); Serial.print(rpy.pitch);
  Serial.print(", Yaw: "); Serial.println(rpy.yaw);

  // Send via NRF24L01
  bool ok = radio.write(&rpy, sizeof(rpy));
  if (!ok) {
    Serial.println("Send failed");
  }

  delay(100);
}
