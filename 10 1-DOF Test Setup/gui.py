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

        # 🔹 Button Colors
        self.reset_btn.setStyleSheet("background-color: goldenrod; font-weight: bold;")
        self.start_btn.setStyleSheet("background-color: green; color: white; font-weight: bold;")
        self.stop_btn.setStyleSheet("background-color: red; color: white; font-weight: bold;")

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
            cb.setStyleSheet("background-color: darkgreen; color: white; font-weight: bold;")

        for btn in [self.motor1_btn, self.motor2_btn, self.motor3_btn, self.motor4_btn]:
            btn.setStyleSheet("background-color: green; color: white; font-weight: bold;")

        for btn, cb in [(self.motor1_btn, self.motor1_pin),
                        (self.motor2_btn, self.motor2_pin),
                        (self.motor3_btn, self.motor3_pin),
                        (self.motor4_btn, self.motor4_pin)]:
            row = QHBoxLayout()
            row.addWidget(btn)
            row.addWidget(cb)
            motor_layout.addLayout(row)

        self.seq_btn = QPushButton("Test All Motors (Seq)")
        self.seq_btn.setStyleSheet("background-color: green; color: white; font-weight: bold;")
        motor_layout.addWidget(self.seq_btn)
        motor_group.setLayout(motor_layout)

        # Wire motor buttons to actions (non-blocking)
        self.motor1_btn.clicked.connect(lambda: self.test_single_motor(self.motor1_pin.currentText()))
        self.motor2_btn.clicked.connect(lambda: self.test_single_motor(self.motor2_pin.currentText()))
        self.motor3_btn.clicked.connect(lambda: self.test_single_motor(self.motor3_pin.currentText()))
        self.motor4_btn.clicked.connect(lambda: self.test_single_motor(self.motor4_pin.currentText()))
        self.seq_btn.clicked.connect(self.run_sequence)

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

        # used to track running sequence state
        self.seq_running = False
        self.seq_index = 0
        self.seq_order = [
            lambda: self.motor1_pin.currentText(),
            lambda: self.motor2_pin.currentText(),
            lambda: self.motor3_pin.currentText(),
            lambda: self.motor4_pin.currentText(),
        ]

        self.load_settings()

    def set_inputs_enabled(self, enabled: bool):
        """Enable/disable all input fields while testing"""
        widgets = [
            self.com_port_select, self.baud_rate_select,
            self.motor1_pin, self.motor2_pin, self.motor3_pin, self.motor4_pin,
            self.mode_select, self.max_roll_input, self.max_pitch_input,
            self.kp_input, self.ki_input, self.kd_input,
            self.test_pwm_input, self.min_pwm_input, self.max_pwm_input,
            self.slider
        ]
        for w in widgets:
            w.setEnabled(enabled)

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
                self.set_inputs_enabled(False)   # 🔹 Disable inputs
                self.timer.start(100)
            except serial.SerialException:
                self.status_label.setText("Error opening port")
        else:
            self.status_label.setText("Status: Cancelled")

    def stop_testing(self):
        # stop any seq in progress
        self.seq_running = False
        self.status_label.setText("Status: Stopped")
        self.timer.stop()
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.roll_label.setText("Roll: --- °")
        self.pitch_label.setText("Pitch: --- °")
        self.set_inputs_enabled(True)   # 🔹 Re-enable inputs

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
                    # auto-range both axes
                    self.error_plot.enableAutoRange(axis=pg.ViewBox.XYAxes, enable=True)

            except Exception:
                pass

    def send_motor_cmd(self, cmd_str: str):
        """Send an ASCII command over serial if open."""
        if self.ser and self.ser.is_open:
            try:
                self.ser.write((cmd_str + "\n").encode())
                self.status_label.setText(f"Sent: {cmd_str}")
            except Exception:
                self.status_label.setText("Error sending command")
        else:
            self.status_label.setText("Port not open")

    def test_single_motor(self, pin_str: str):
        """Start motor at GUI test PWM for 5 seconds then stop (non-blocking)."""
        try:
            pwm = int(self.test_pwm_input.text())
        except Exception:
            self.status_label.setText("Invalid PWM")
            return

        start_cmd = f"MOTOR START {pin_str} {pwm}"
        stop_cmd = f"MOTOR STOP {pin_str}"

        # send start
        self.send_motor_cmd(start_cmd)

        # stop after 5 seconds (5000 ms)
        QTimer.singleShot(5000, lambda: self.send_motor_cmd(stop_cmd))

    def run_sequence(self):
        """Run motors 1..4 each for 5s with 2s gap (non-blocking)."""
        if self.seq_running:
            self.status_label.setText("Sequence already running")
            return

        try:
            pwm = int(self.test_pwm_input.text())
        except Exception:
            self.status_label.setText("Invalid PWM")
            return

        # lock UI while sequence runs
        self.seq_running = True
        self.set_inputs_enabled(False)
        self.seq_index = 0
        self._run_seq_step(pwm)

    def _run_seq_step(self, pwm):
        if not self.seq_running or self.seq_index >= len(self.seq_order):
            # finished
            self.seq_running = False
            self.set_inputs_enabled(True)
            self.status_label.setText("Sequence finished")
            return

        pin = self.seq_order[self.seq_index]()
        start_cmd = f"MOTOR START {pin} {pwm}"
        stop_cmd = f"MOTOR STOP {pin}"

        # start motor
        self.send_motor_cmd(start_cmd)

        # schedule stop after 5s, then schedule next step after (5s + 2s gap)
        QTimer.singleShot(5000, lambda: self.send_motor_cmd(stop_cmd))
        # next step after 7s from now (5000ms runtime + 2000ms gap)
        QTimer.singleShot(7000, self._advance_seq)

    def _advance_seq(self):
        self.seq_index += 1
        # continue sequence
        self._run_seq_step(int(self.test_pwm_input.text()))

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
