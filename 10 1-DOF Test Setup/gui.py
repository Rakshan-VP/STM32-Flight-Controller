import sys
import serial
import re
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QHBoxLayout, QVBoxLayout,
    QGroupBox, QLineEdit, QComboBox, QSlider, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, QSettings

# Import dark theme
import dark_theme

SERIAL_PORT = "COM3"   # Change as needed
BAUD_RATE = 9600


class TestSetupGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("1 DOF Test Setup")
        self.setGeometry(200, 200, 800, 400)

        self.ser = None  # Serial object
        self.settings = QSettings("MyCompany", "TestSetupGUI")

        # --- Buttons ---
        self.reset_btn = QPushButton("Reset to Default")
        self.start_btn = QPushButton("Start Testing")
        self.stop_btn = QPushButton("Stop Testing")

        # --- Status Label ---
        self.status_label = QLabel("Status: Stopped")
        self.status_label.setAlignment(Qt.AlignCenter)

        # --- Roll & Pitch Labels ---
        self.roll_label = QLabel("Roll: --- °")
        self.pitch_label = QLabel("Pitch: --- °")
        self.roll_label.setAlignment(Qt.AlignCenter)
        self.pitch_label.setAlignment(Qt.AlignCenter)

        # Connect buttons
        self.start_btn.clicked.connect(self.start_testing)
        self.stop_btn.clicked.connect(self.stop_testing)
        self.reset_btn.clicked.connect(self.reset_to_default)

        # --- Layouts for top part ---
        top_layout = QHBoxLayout()

        # Left: Reset button
        top_layout.addWidget(self.reset_btn)

        # Center: Status label
        top_layout.addStretch()
        top_layout.addWidget(self.status_label, alignment=Qt.AlignCenter)
        top_layout.addStretch()

        # Right: Start/Stop buttons
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.stop_btn)
        top_layout.addLayout(btn_row)
        
        # --- Test Motor Group (VERTICAL buttons + dropdowns) ---
        motor_group = QGroupBox("Test Motor")
        motor_layout = QVBoxLayout()

        # Pin options
        pin_options = ["A0", "A1", "B4", "B5", "A15", "A11", "A10", "A9", "B13", "B14", "B15", "A8"]

        # Motor 1
        row1 = QHBoxLayout()
        self.motor1_btn = QPushButton("Test Motor 1")
        self.motor1_pin = QComboBox()
        self.motor1_pin.addItems(pin_options)
        row1.addWidget(self.motor1_btn)
        row1.addWidget(self.motor1_pin)
        motor_layout.addLayout(row1)

        # Motor 2
        row2 = QHBoxLayout()
        self.motor2_btn = QPushButton("Test Motor 2")
        self.motor2_pin = QComboBox()
        self.motor2_pin.addItems(pin_options)
        row2.addWidget(self.motor2_btn)
        row2.addWidget(self.motor2_pin)
        motor_layout.addLayout(row2)

        # Motor 3
        row3 = QHBoxLayout()
        self.motor3_btn = QPushButton("Test Motor 3")
        self.motor3_pin = QComboBox()
        self.motor3_pin.addItems(pin_options)
        row3.addWidget(self.motor3_btn)
        row3.addWidget(self.motor3_pin)
        motor_layout.addLayout(row3)

        # Motor 4
        row4 = QHBoxLayout()
        self.motor4_btn = QPushButton("Test Motor 4")
        self.motor4_pin = QComboBox()
        self.motor4_pin.addItems(pin_options)
        row4.addWidget(self.motor4_btn)
        row4.addWidget(self.motor4_pin)
        motor_layout.addLayout(row4)

        # Sequential Test
        row5 = QHBoxLayout()
        self.seq_btn = QPushButton("Test All Motors (Seq)")
        row5.addWidget(self.seq_btn)
        motor_layout.addLayout(row5)

        motor_group.setLayout(motor_layout)

        # Connect motor test buttons
        self.motor1_btn.clicked.connect(lambda: self.send_motor_cmd(f"M1:{self.motor1_pin.currentText()}"))
        self.motor2_btn.clicked.connect(lambda: self.send_motor_cmd(f"M2:{self.motor2_pin.currentText()}"))
        self.motor3_btn.clicked.connect(lambda: self.send_motor_cmd(f"M3:{self.motor3_pin.currentText()}"))
        self.motor4_btn.clicked.connect(lambda: self.send_motor_cmd(f"M4:{self.motor4_pin.currentText()}"))
        self.seq_btn.clicked.connect(lambda: self.send_motor_cmd(f"SEQ:{self.seq_btn.connectNotify()}"))


        # --- PID Values Group ---
        pid_group = QGroupBox("PID Values")
        pid_layout = QVBoxLayout()

        # Dropdown + Max Roll/Pitch
        top_row = QHBoxLayout()
        self.mode_select = QComboBox()
        self.mode_select.addItems(["Roll", "Pitch"])
        self.max_roll_input = QLineEdit()
        self.max_pitch_input = QLineEdit()
        top_row.addWidget(self.mode_select)
        top_row.addWidget(QLabel("Max Roll:"))
        top_row.addWidget(self.max_roll_input)
        top_row.addWidget(QLabel("Max Pitch:"))
        top_row.addWidget(self.max_pitch_input)

        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(-100)
        self.slider.setMaximum(100)
        self.slider.setValue(0)  # Default center

        # PID values in one line
        pid_row = QHBoxLayout()
        self.kp_input = QLineEdit()
        self.ki_input = QLineEdit()
        self.kd_input = QLineEdit()
        pid_row.addWidget(QLabel("Kp:"))
        pid_row.addWidget(self.kp_input)
        pid_row.addWidget(QLabel("Ki:"))
        pid_row.addWidget(self.ki_input)
        pid_row.addWidget(QLabel("Kd:"))
        pid_row.addWidget(self.kd_input)

        # Add all to layout
        pid_layout.addLayout(top_row)
        pid_layout.addWidget(self.slider)
        pid_layout.addLayout(pid_row)
        pid_group.setLayout(pid_layout)

        # --- Parameters Group ---
        param_group = QGroupBox("Parameters")
        param_layout = QHBoxLayout()

        self.test_pwm_input = QLineEdit()
        self.min_pwm_input = QLineEdit()
        self.max_pwm_input = QLineEdit()

        param_layout.addWidget(QLabel("Testing PWM:"))
        param_layout.addWidget(self.test_pwm_input)
        param_layout.addWidget(QLabel("Min PWM:"))
        param_layout.addWidget(self.min_pwm_input)
        param_layout.addWidget(QLabel("Max PWM:"))
        param_layout.addWidget(self.max_pwm_input)

        param_group.setLayout(param_layout)

        # --- Groups side by side ---
        groups_layout = QHBoxLayout()
        groups_layout.addWidget(motor_group)
        groups_layout.addWidget(pid_group)

        # --- Main Layout ---
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)

        # Add roll & pitch values
        values_layout = QHBoxLayout()
        values_layout.addWidget(self.roll_label)
        values_layout.addWidget(self.pitch_label)
        main_layout.addLayout(values_layout)

        main_layout.addLayout(groups_layout)
        main_layout.addWidget(param_group)

        self.setLayout(main_layout)

        # --- Timer for reading serial ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.read_serial_data)

        # Load stored settings
        self.load_settings()

    def start_testing(self):
        # --- Popup Warning ---
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Safety Check")
        msg.setText("⚠️ Make sure:\n\n"
                    "1. Propellers are connected properly\n"
                    "2. Drone is securely placed in the test stand\n\n"
                    "Do you want to continue?")
        msg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        msg.button(QMessageBox.Ok).setText("Confirm")
        msg.button(QMessageBox.Cancel).setText("Cancel")

        result = msg.exec_()

        if result == QMessageBox.Ok:
            try:
                self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
                self.status_label.setText("Status: Started")
                self.timer.start(100)  # read every 100 ms
            except serial.SerialException:
                self.status_label.setText("Error opening port")
        else:
            self.status_label.setText("Status: Cancelled")

    def stop_testing(self):
        self.status_label.setText("Status: Stopped")
        self.timer.stop()
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.roll_label.setText("Roll: --- °")
        self.pitch_label.setText("Pitch: --- °")

    def read_serial_data(self):
        if self.ser and self.ser.in_waiting > 0:
            try:
                line = self.ser.readline().decode('utf-8').strip()
                # Expected format: R:12.34,P:-5.67
                match = re.match(r"R:([-+]?\d*\.\d+|\d+),P:([-+]?\d*\.\d+|\d+)", line)
                if match:
                    roll = float(match.group(1))
                    pitch = float(match.group(2))
                    self.roll_label.setText(f"Roll: {roll:.2f} °")
                    self.pitch_label.setText(f"Pitch: {pitch:.2f} °")
            except Exception:
                pass

    def send_motor_cmd(self, cmd):
        """Send motor test command to STM32 via serial"""
        if self.ser and self.ser.is_open:
            try:
                self.ser.write((cmd + "\n").encode())
                self.status_label.setText(f"Sent: {cmd}")
            except Exception:
                self.status_label.setText("Error sending command")
        else:
            self.status_label.setText("Port not open")

    def reset_to_default(self):
        """Reset all inputs to default values"""
        self.mode_select.setCurrentIndex(0)
        self.max_roll_input.setText("15")
        self.max_pitch_input.setText("15")
        self.kp_input.setText("1.0")
        self.ki_input.setText("0.0")
        self.kd_input.setText("0.0")
        self.test_pwm_input.setText("1200")
        self.min_pwm_input.setText("1100")
        self.max_pwm_input.setText("1500")
        self.slider.setValue(0)

    def closeEvent(self, event):
        """Save settings when closing"""
        self.settings.setValue("mode", self.mode_select.currentIndex())
        self.settings.setValue("max_roll", self.max_roll_input.text())
        self.settings.setValue("max_pitch", self.max_pitch_input.text())
        self.settings.setValue("kp", self.kp_input.text())
        self.settings.setValue("ki", self.ki_input.text())
        self.settings.setValue("kd", self.kd_input.text())
        self.settings.setValue("test_pwm", self.test_pwm_input.text())
        self.settings.setValue("min_pwm", self.min_pwm_input.text())
        self.settings.setValue("max_pwm", self.max_pwm_input.text())
        # Slider is NOT saved
        event.accept()

    def load_settings(self):
        """Load stored settings"""
        self.mode_select.setCurrentIndex(int(self.settings.value("mode", 0)))
        self.max_roll_input.setText(self.settings.value("max_roll", "15"))
        self.max_pitch_input.setText(self.settings.value("max_pitch", "15"))
        self.kp_input.setText(self.settings.value("kp", "1.0"))
        self.ki_input.setText(self.settings.value("ki", "0.0"))
        self.kd_input.setText(self.settings.value("kd", "0.0"))
        self.test_pwm_input.setText(self.settings.value("test_pwm", "1200"))
        self.min_pwm_input.setText(self.settings.value("min_pwm", "1100"))
        self.max_pwm_input.setText(self.settings.value("max_pwm", "1500"))
        self.slider.setValue(0)  # Always reset slider


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Apply dark theme
    app.setStyleSheet(dark_theme.dark_stylesheet)
    window = TestSetupGUI()
    window.show()
    sys.exit(app.exec_())
