// fc.ino - modified to receive commands via RF, run PID, send telemetry
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Servo.h>
#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

// ---- I2C buses ----
TwoWire Wire1(PB7, PB6);
TwoWire Wire2(PB3, PB10);

// ---- IMU objects ----
Adafruit_MPU6050 imu1;
Adafruit_MPU6050 imu2;

// ---- Motors ----
Servo M1, M2, M3, M4;
const int MOTOR_PIN_1 = PB4; //front right
const int MOTOR_PIN_2 = PA1; //front left
const int MOTOR_PIN_3 = PB5; //rear right
const int MOTOR_PIN_4 = PA0; //rear left

const int PWM_MIN  = 1150;
const int PWM_MAX  = 1400; // extended up for safety
const int PWM_MID  = (PWM_MIN + PWM_MAX) / 2;

const float alpha = 0.98f;
float roll1=0, pitch1=0, roll2=0, pitch2=0;
float roll=0, pitch=0;

// PID terms (set from GCS)
float Kp = 0.0f, Ki = 0.0f, Kd = 0.0f;
float desired = 0.0f;
uint8_t axis_select = 0; // 0=roll, 1=pitch
bool running = false;

// PID state
float integ = 0.0f;
float last_error = 0.0f;

// timing
unsigned long lastTime = 0;

// ---- RF24 ----
// We'll use two addresses: telemetry (FC->GCS) and commands (GCS->FC)
const byte address_tx[6] = "00001"; // telemetry from FC
const byte address_rx[6] = "00002"; // commands to FC

#define CE_PIN PB0
#define CSN_PIN PA4
RF24 radio(CE_PIN, CSN_PIN);

// Packed telemetry struct (FC -> GCS)
struct __attribute__((packed)) Telemetry {
  float roll_error;
  float pitch_error;
  int16_t pwm1, pwm2, pwm3, pwm4;
};
Telemetry data;

// Command struct (GCS -> FC)
struct __attribute__((packed)) Command {
  uint8_t cmd; // 0 = STOP, 1 = START, 2 = UPDATE (update params)
  uint8_t axis; // 0 roll, 1 pitch
  float setpoint;
  float kp, ki, kd;
};
Command cmdBuf;

void setup() {
  Serial.begin(115200);

  Wire1.begin();
  Wire2.begin();

  if (! imu1.begin(MPU6050_I2CADDR_DEFAULT, &Wire1)) while (1);
  if (! imu2.begin(MPU6050_I2CADDR_DEFAULT, &Wire2)) while (1);
  imu1.setAccelerometerRange(MPU6050_RANGE_4_G);
  imu1.setGyroRange(MPU6050_RANGE_500_DEG);
  imu1.setFilterBandwidth(MPU6050_BAND_21_HZ);
  imu2.setAccelerometerRange(MPU6050_RANGE_4_G);
  imu2.setGyroRange(MPU6050_RANGE_500_DEG);
  imu2.setFilterBandwidth(MPU6050_BAND_21_HZ);

  M1.attach(MOTOR_PIN_1);
  M2.attach(MOTOR_PIN_2);
  M3.attach(MOTOR_PIN_3);
  M4.attach(MOTOR_PIN_4);

  // default safe PID
  Kp = 0.0f; Ki = 0.0f; Kd = 0.0f;

  // Stop motors (safe idle)
  M1.writeMicroseconds(1000);
  M2.writeMicroseconds(1000);
  M3.writeMicroseconds(1000);
  M4.writeMicroseconds(1000);

  delay(300);

  // Setup radio:
  radio.begin();
  // Telemetry pipe (write)
  radio.openWritingPipe(address_tx);
  // Command pipe (read)
  radio.openReadingPipe(0, address_rx);
  radio.setPALevel(RF24_PA_MIN);
  // Start listening for commands
  radio.startListening();

  lastTime = millis();
}

void fuseDroneAxes(const sensors_event_t &a, const sensors_event_t &g,
                   float &roll_est, float &pitch_est, float dt) {
  float ax=a.acceleration.x, ay=a.acceleration.y, az=a.acceleration.z;
  float gx=g.gyro.x, gy=g.gyro.y;

  float ax_d=ay, ay_d=-ax, az_d=az;
  float gx_d=gy, gy_d=-gx;

  float accRoll=atan2(ay_d, az_d)*180.0f/PI;
  float accPitch=atan2(-ax_d, sqrt(ay_d*ay_d+az_d*az_d))*180.0f/PI;
  float gyroRollRate=gx_d*180.0f/PI;
  float gyroPitchRate=gy_d*180.0f/PI;

  roll_est = alpha*(roll_est+gyroRollRate*dt)+(1-alpha)*accRoll;
  pitch_est= alpha*(pitch_est+gyroPitchRate*dt)+(1-alpha)*accPitch;
}

void checkForCommand() {
  // radio is listening; check if command arrived
  if (radio.available()) {
    while (radio.available()) {
      radio.read(&cmdBuf, sizeof(cmdBuf));
    }
    // Process last command received
    if (cmdBuf.cmd == 0) { // STOP
      running = false;
      integ = 0.0f;
      last_error = 0.0f;
      // stop motors -> safe idle
      M1.writeMicroseconds(1000);
      M2.writeMicroseconds(1000);
      M3.writeMicroseconds(1000);
      M4.writeMicroseconds(1000);
    } else if (cmdBuf.cmd == 1) { // START
      // Update parameters then do ESC init then start
      axis_select = cmdBuf.axis;
      desired = cmdBuf.setpoint;
      Kp = cmdBuf.kp; Ki = cmdBuf.ki; Kd = cmdBuf.kd;

      // ESC initialization sequence (4 seconds)
      running = false;
      M1.writeMicroseconds(1000);
      M2.writeMicroseconds(1000);
      M3.writeMicroseconds(1000);
      M4.writeMicroseconds(1000);
      delay(4000);
      // Reset integrator and last error
      integ = 0.0f;
      last_error = 0.0f;
      lastTime = millis();
      running = true;
    } else if (cmdBuf.cmd == 2) { // UPDATE PID/SETPOINT without re-init
      axis_select = cmdBuf.axis;
      desired = cmdBuf.setpoint;
      Kp = cmdBuf.kp; Ki = cmdBuf.ki; Kd = cmdBuf.kd;
    }
  }
}

void loop() {
  unsigned long now=millis();
  float dt=(now-lastTime)/1000.0f;
  if(dt<=0) dt=0.001f;
  lastTime=now;

  // First check for incoming commands (we are listening)
  checkForCommand();

  // Read IMUs
  sensors_event_t acc1, gyro1, t1;
  imu1.getEvent(&acc1, &gyro1, &t1);
  fuseDroneAxes(acc1, gyro1, roll1, pitch1, dt);

  sensors_event_t acc2, gyro2, t2;
  imu2.getEvent(&acc2, &gyro2, &t2);
  fuseDroneAxes(acc2, gyro2, roll2, pitch2, dt);

  roll=(roll1+roll2)*0.5f;
  pitch=(pitch1+pitch2)*0.5f;

  // Default pwms are idle
  int pwm1 = PWM_MIN;
  int pwm2 = PWM_MIN;
  int pwm3 = PWM_MIN;
  int pwm4 = PWM_MIN;

  float roll_error = 0.0f;
  float pitch_error = 0.0f;

  if (running) {
    float measurement = (axis_select==0) ? roll : pitch;
    float error = desired - measurement;
    // PID
    integ += error * dt;
    // anti-windup: clamp integral to reasonable bounds
    float integ_max = 1000.0f;
    if (integ > integ_max) integ = integ_max;
    if (integ < -integ_max) integ = -integ_max;
    float deriv = (dt>0.0f) ? (error - last_error)/dt : 0.0f;
    float corr = Kp*error + Ki*integ + Kd*deriv;
    last_error = error;

    // Set roll_error and pitch_error values for telemetry (both populated)
    if (axis_select==0) {
      roll_error = error;
      pitch_error = pitch - 0.0f; // no commanded pitch
    } else {
      pitch_error = error;
      roll_error = roll - 0.0f;
    }

    // Mixer: simple X config mapping
    // pwmM = PWM_MID +/- roll_corr +/- pitch_corr
    // corr value scaled to PWM counts; we assume Kp etc. are in PWM-per-degree units
    int corr = int(corr);
    // For clarity split roll/pitch contributions:
    // We'll compute roll_corr and pitch_corr from pid contributions (approx)
    // But here corr is combined. To keep behaviour similar to previous, do:
    float roll_corr_f = Kp * ((axis_select==0)? error : 0.0f); // only if controlling roll
    float pitch_corr_f = Kp * ((axis_select==1)? error : 0.0f);
    // incorporate integral/derivative roughly - better to map using combined corr:
    // To avoid complexity, use combined corr distributed
    int combined = int(Kp*error + Ki*integ + Kd*deriv);

    // Use combined to affect both axes appropriately:
    if (axis_select==0) {
      // roll control: adjust left/right
      pwm1 = int(PWM_MID - combined); // front right
      pwm2 = int(PWM_MID + combined); // front left
      pwm3 = int(PWM_MID - combined); // rear right
      pwm4 = int(PWM_MID + combined); // rear left
    } else {
      // pitch control: adjust front/back
      pwm1 = int(PWM_MID - combined); // front right (front down)
      pwm2 = int(PWM_MID - combined); // front left
      pwm3 = int(PWM_MID + combined); // rear right
      pwm4 = int(PWM_MID + combined); // rear left
    }

    // Mix both axes loosely if needed - for simplicity above is ok.

    // constrain
    pwm1 = constrain(pwm1, PWM_MIN, PWM_MAX);
    pwm2 = constrain(pwm2, PWM_MIN, PWM_MAX);
    pwm3 = constrain(pwm3, PWM_MIN, PWM_MAX);
    pwm4 = constrain(pwm4, PWM_MIN, PWM_MAX);

    // Write to motors
    M1.writeMicroseconds(pwm1);
    M2.writeMicroseconds(pwm2);
    M3.writeMicroseconds(pwm3);
    M4.writeMicroseconds(pwm4);
  } else {
    // not running -> idle
    M1.writeMicroseconds(1000);
    M2.writeMicroseconds(1000);
    M3.writeMicroseconds(1000);
    M4.writeMicroseconds(1000);
    // compute errors for telemetry
    roll_error = 0.0f;
    pitch_error = 0.0f;
    pwm1 = pwm2 = pwm3 = pwm4 = 1000;
  }

  // Pack telemetry
  data.roll_error = roll_error;
  data.pitch_error = pitch_error;
  data.pwm1 = pwm1; data.pwm2 = pwm2; data.pwm3 = pwm3; data.pwm4 = pwm4;

  // Send telemetry: we must stopListening to write
  radio.stopListening();
  radio.write(&data, sizeof(data));
  // back to listening for next command
  radio.startListening();

  delay(20); // run ~50 Hz telemetry
}
