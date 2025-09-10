// gcs.ino - receives serial commands from PC (GUI), forwards commands to FC via RF,
// and relays telemetry from FC to PC serial.

#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

#define CE_PIN 6
#define CSN_PIN 7
RF24 radio(CE_PIN, CSN_PIN);

// Telemetry struct (same as FC)
struct __attribute__((packed)) Telemetry {
  float roll_error;
  float pitch_error;
  int16_t pwm1, pwm2, pwm3, pwm4;
};
Telemetry data;

// Command struct (same as FC)
struct __attribute__((packed)) Command {
  uint8_t cmd; // 0 = STOP, 1 = START, 2 = UPDATE
  uint8_t axis; // 0 roll, 1 pitch
  float setpoint;
  float kp, ki, kd;
};

Command cmdOut;

// Addressing: GCS <-> FC
const byte address_tx[6] = "00002"; // GCS -> FC (commands)
const byte address_rx[6] = "00001"; // FC -> GCS (telemetry)

void setup() {
  Serial.begin(115200);
  // radio setup
  radio.begin();
  // commands: write to 00002
  radio.openWritingPipe(address_tx);
  // telemetry: read from 00001
  radio.openReadingPipe(0, address_rx);
  radio.setPALevel(RF24_PA_MIN);
  radio.startListening();
}

String readSerialLine() {
  static String line = "";
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n') {
      String out = line;
      line = "";
      return out;
    } else if (c == '\r') {
      // ignore
    } else {
      line += c;
    }
  }
  return String(""); // empty when nothing complete
}

void forwardCommandToFC(Command &c) {
  // stop listening, write, then listen again
  radio.stopListening();
  bool ok = radio.write(&c, sizeof(c));
  radio.startListening();
  // optional: ack via Serial
  if (!ok) {
    Serial.println("ERR_TX");
  }
}

void loop() {
  // 1) Check for telemetry from FC and print to serial for GUI
  if (radio.available()) {
    while (radio.available()) {
      radio.read(&data, sizeof(data));
    }
    // print CSV line: roll_error,pitch_error,m1,m2,m3,m4\n
    Serial.print(data.roll_error); Serial.print(",");
    Serial.print(data.pitch_error); Serial.print(",");
    Serial.print(data.pwm1); Serial.print(",");
    Serial.print(data.pwm2); Serial.print(",");
    Serial.print(data.pwm3); Serial.print(",");
    Serial.println(data.pwm4);
  }

  // 2) Check for incoming serial command from GUI
  String line = readSerialLine();
  if (line.length() > 0) {
    // expected formats:
    // START,ROLL,angle,Kp,Ki,Kd
    // START,PITCH,angle,Kp,Ki,Kd
    // STOP
    // UPDATE,ROLL,angle,Kp,Ki,Kd  (update params without ESC init)
    line.trim();
    if (line.equalsIgnoreCase("STOP")) {
      cmdOut.cmd = 0;
      forwardCommandToFC(cmdOut);
      Serial.println("ACK_STOP");
    } else {
      // split by commas
      // convert to tokens
      const int maxT = 8;
      String tokens[maxT];
      int tcount = 0;
      int start = 0;
      for (int i=0;i<line.length()+1 && tcount<maxT;i++) {
        if (i==line.length() || line.charAt(i) == ',') {
          tokens[tcount++] = line.substring(start, i);
          start = i+1;
        }
      }
      if (tcount >= 1) {
        String cmdTok = tokens[0];
        if (cmdTok.equalsIgnoreCase("START") || cmdTok.equalsIgnoreCase("UPDATE")) {
          bool isStart = cmdTok.equalsIgnoreCase("START");
          cmdOut.cmd = isStart ? 1 : 2;
          // tokens[1] axis
          String axisTok = (tcount>1)?tokens[1]:"ROLL";
          cmdOut.axis = axisTok.equalsIgnoreCase("PITCH") ? 1 : 0;
          // setpoint
          cmdOut.setpoint = (tcount>2)? tokens[2].toFloat() : 0.0f;
          cmdOut.kp = (tcount>3)? tokens[3].toFloat() : 0.0f;
          cmdOut.ki = (tcount>4)? tokens[4].toFloat() : 0.0f;
          cmdOut.kd = (tcount>5)? tokens[5].toFloat() : 0.0f;
          forwardCommandToFC(cmdOut);
          Serial.println("ACK_CMD");
        } else {
          Serial.println("ERR_CMD");
        }
      } else {
        Serial.println("ERR_PARSE");
      }
    }
  }

  // tiny sleep
  delay(5);
}
