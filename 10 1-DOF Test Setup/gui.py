import sys
import serial
import re
import serial.tools.list_ports as list_ports
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QHBoxLayout, QVBoxLayout,
    QGroupBox, QLineEdit, QComboBox, QSlider, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, QSettings
import pyqtgraph as pg
import dark_theme


class TestSetupGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("1 DOF Test Setup")
        self.setGeometry(200, 200, 900, 600)

        self.ser = None
        self.settings = QSettings("MyCompany", "TestSetupGUI")

        # --- Data storage for plotting ---
        self.time_data = []
        self.error_data = []
        self.start_time = 0
        self.sample_count = 0

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

        # Left: Reset button + COM/BAUD selectors
        left_layout = QHBoxLayout()
        self.com_port_select = QComboBox()
        ports = [port.device for port in list_ports.comports()]
        self.com_port_select.addItems(ports if ports else ["No Ports"])

        self.baud_rate_select = QComboBox()
        self.baud_rate_select.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baud_rate_select.setCurrentText("9600")

        left_layout.addWidget(self.reset_btn)
        left_layout.addWidget(QLabel("Port:"))
        left_layout.addWidget(self.com_port_select)
        left_layout.addWidget(QLabel("Baud:"))
        left_layout.addWidget(self.baud_rate_select)

        top_layout.addLayout(left_layout)

        # Center: Status label
        top_layout.addStretch()
        top_layout.addWidget(self.status_label, alignment=Qt.AlignCenter)
        top_layout.addStretch()

        # Right: Start/Stop buttons
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.stop_btn)
        top_layout.addLayout(btn_row)

        # --- Motor Group ---
        motor_group = QGroupBox("Test Motor")
        motor_layout = QVBoxLayout()
        pin_options = ["A0", "A1", "B4", "B5", "A15", "A11", "A10", "A9", "B13", "B14", "B15", "A8"]

        self.motor1_btn, self.motor1_pin = QPushButton("Test Motor 1"), QComboBox()
        self.motor2_btn, self.motor2_pin = QPushButton("Test Motor 2"), QComboBox()
        self.motor3_btn, self.motor3_pin = QPushButton("Test Motor 3"), QComboBox()
        self.motor4_btn, self.motor4_pin = QPushButton("Test Motor 4"), QComboBox()
        for cb in [self.motor1_pin, self.motor2_pin, self.motor3_pin, self.motor4_pin]:
            cb.addItems(pin_options)

        for btn, cb in [(self.motor1_btn, self.motor1_pin),
                        (self.motor2_btn, self.motor2_pin),
                        (self.motor3_btn, self.motor3_pin),
                        (self.motor4_btn, self.motor4_pin)]:
            row = QHBoxLayout()
            row.addWidget(btn)
            row.addWidget(cb)
            motor_layout.addLayout(row)

        self.seq_btn = QPushButton("Test All Motors (Seq)")
        motor_layout.addWidget(self.seq_btn)
        motor_group.setLayout(motor_layout)

        self.motor1_btn.clicked.connect(lambda: self.send_motor_cmd(f"M1:{self.motor1_pin.currentText()}"))
        self.motor2_btn.clicked.connect(lambda: self.send_motor_cmd(f"M2:{self.motor2_pin.currentText()}"))
        self.motor3_btn.clicked.connect(lambda: self.send_motor_cmd(f"M3:{self.motor3_pin.currentText()}"))
        self.motor4_btn.clicked.connect(lambda: self.send_motor_cmd(f"M4:{self.motor4_pin.currentText()}"))
        self.seq_btn.clicked.connect(lambda: self.send_motor_cmd("SEQ"))

        # --- PID Values Group ---
        pid_group = QGroupBox("PID Values")
        pid_layout = QVBoxLayout()
        top_row = QHBoxLayout()
        self.mode_select = QComboBox()
        self.mode_select.addItems(["Roll", "Pitch"])
        self.max_roll_input, self.max_pitch_input = QLineEdit(), QLineEdit()
        top_row.addWidget(self.mode_select)
        top_row.addWidget(QLabel("Max Roll:"))
        top_row.addWidget(self.max_roll_input)
        top_row.addWidget(QLabel("Max Pitch:"))
        top_row.addWidget(self.max_pitch_input)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(-100, 100)
        self.slider.setValue(0)

        pid_row = QHBoxLayout()
        self.kp_input, self.ki_input, self.kd_input = QLineEdit(), QLineEdit(), QLineEdit()
        for lbl, inp in [("Kp:", self.kp_input), ("Ki:", self.ki_input), ("Kd:", self.kd_input)]:
            pid_row.addWidget(QLabel(lbl))
            pid_row.addWidget(inp)

        pid_layout.addLayout(top_row)
        pid_layout.addWidget(self.slider)
        pid_layout.addLayout(pid_row)
        pid_group.setLayout(pid_layout)

        # --- Parameters Group ---
        param_group = QGroupBox("Parameters")
        param_layout = QHBoxLayout()
        self.test_pwm_input, self.min_pwm_input, self.max_pwm_input = QLineEdit(), QLineEdit(), QLineEdit()
        for lbl, inp in [("Testing PWM:", self.test_pwm_input),
                         ("Min PWM:", self.min_pwm_input),
                         ("Max PWM:", self.max_pwm_input)]:
            param_layout.addWidget(QLabel(lbl))
            param_layout.addWidget(inp)
        param_group.setLayout(param_layout)

        # --- Groups side by side ---
        groups_layout = QHBoxLayout()
        groups_layout.addWidget(motor_group)
        groups_layout.addWidget(pid_group)

        # --- Error vs Time Plot ---
        self.error_plot = pg.PlotWidget(title="Error vs Time")
        self.error_plot.showGrid(x=True, y=True)
        self.error_plot.setLabel("left", "Error", units="°")
        self.error_plot.setLabel("bottom", "Time", units="s")
        self.error_curve = self.error_plot.plot(pen="y")

        # --- Main Layout ---
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)

        values_layout = QHBoxLayout()
        values_layout.addWidget(self.roll_label)
        values_layout.addWidget(self.pitch_label)
        main_layout.addLayout(values_layout)

        main_layout.addLayout(groups_layout)
        main_layout.addWidget(param_group)

        # 🔹 Add Error Plot at bottom
        main_layout.addWidget(self.error_plot)

        self.setLayout(main_layout)

        # --- Timer ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.read_serial_data)

        self.load_settings()

    def start_testing(self):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Safety Check")
        msg.setText("⚠️ Make sure:\n\n1. Props are attached\n2. Drone is secured\n\nContinue?")
        msg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        msg.button(QMessageBox.Ok).setText("Confirm")
        msg.button(QMessageBox.Cancel).setText("Cancel")
        result = msg.exec_()

        if result == QMessageBox.Ok:
            try:
                port = self.com_port_select.currentText()
                baud = int(self.baud_rate_select.currentText())
                self.ser = serial.Serial(port, baud, timeout=1)
                self.status_label.setText(f"Status: Started ({port}, {baud})")
                self.time_data.clear()
                self.error_data.clear()
                self.sample_count = 0
                self.timer.start(100)
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
                line = self.ser.readline().decode("utf-8").strip()
                match = re.match(r"R:([-+]?\d*\.\d+|\d+),P:([-+]?\d*\.\d+|\d+)", line)
                if match:
                    roll, pitch = float(match.group(1)), float(match.group(2))
                    self.roll_label.setText(f"Roll: {roll:.2f} °")
                    self.pitch_label.setText(f"Pitch: {pitch:.2f} °")

                    # Compute error (example: roll - pitch)
                    error = roll - pitch
                    self.sample_count += 1
                    self.time_data.append(self.sample_count * 0.1)  # 0.1s step (100ms)
                    self.error_data.append(error)

                    # Update plot
                    self.error_curve.setData(self.time_data, self.error_data)
                    self.error_plot.enableAutoRange(axis=pg.ViewBox.XYAxes, enable=True)

            except Exception:
                pass

    def send_motor_cmd(self, cmd):
        if self.ser and self.ser.is_open:
            try:
                self.ser.write((cmd + "\n").encode())
                self.status_label.setText(f"Sent: {cmd}")
            except Exception:
                self.status_label.setText("Error sending command")
        else:
            self.status_label.setText("Port not open")

    def reset_to_default(self):
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
        self.settings.setValue("mode", self.mode_select.currentIndex())
        self.settings.setValue("max_roll", self.max_roll_input.text())
        self.settings.setValue("max_pitch", self.max_pitch_input.text())
        self.settings.setValue("kp", self.kp_input.text())
        self.settings.setValue("ki", self.ki_input.text())
        self.settings.setValue("kd", self.kd_input.text())
        self.settings.setValue("test_pwm", self.test_pwm_input.text())
        self.settings.setValue("min_pwm", self.min_pwm_input.text())
        self.settings.setValue("max_pwm", self.max_pwm_input.text())
        self.settings.setValue("com_port", self.com_port_select.currentText())
        self.settings.setValue("baud_rate", self.baud_rate_select.currentText())
        self.settings.setValue("motor1_pin", self.motor1_pin.currentText())
        self.settings.setValue("motor2_pin", self.motor2_pin.currentText())
        self.settings.setValue("motor3_pin", self.motor3_pin.currentText())
        self.settings.setValue("motor4_pin", self.motor4_pin.currentText())
        event.accept()

    def load_settings(self):
        self.mode_select.setCurrentIndex(int(self.settings.value("mode", 0)))
        self.max_roll_input.setText(self.settings.value("max_roll", "15"))
        self.max_pitch_input.setText(self.settings.value("max_pitch", "15"))
        self.kp_input.setText(self.settings.value("kp", "1.0"))
        self.ki_input.setText(self.settings.value("ki", "0.0"))
        self.kd_input.setText(self.settings.value("kd", "0.0"))
        self.test_pwm_input.setText(self.settings.value("test_pwm", "1200"))
        self.min_pwm_input.setText(self.settings.value("min_pwm", "1100"))
        self.max_pwm_input.setText(self.settings.value("max_pwm", "1500"))
        self.slider.setValue(0)

        for combo, key in [(self.com_port_select, "com_port"),
                           (self.baud_rate_select, "baud_rate"),
                           (self.motor1_pin, "motor1_pin"),
                           (self.motor2_pin, "motor2_pin"),
                           (self.motor3_pin, "motor3_pin"),
                           (self.motor4_pin, "motor4_pin")]:
            val = self.settings.value(key, "")
            if val:
                idx = combo.findText(val)
                if idx >= 0:
                    combo.setCurrentIndex(idx)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(dark_theme.dark_stylesheet)
    window = TestSetupGUI()
    window.show()
    sys.exit(app.exec_())
