# gui.py - modified GUI to send start/stop/axis/setpoint/PID to GCS Arduino,
# lock values while running, toggle start->stop, and continue plotting telemetry.

import sys, serial, threading, serial.tools.list_ports, csv, datetime, os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton,
                             QComboBox, QLabel, QHBoxLayout, QLineEdit, QDoubleSpinBox, QGridLayout)
from PyQt5.QtCore import pyqtSignal, QObject, Qt
import pyqtgraph as pg

# ---- Serial reader thread ----
class SerialReader(QObject):
    data_received = pyqtSignal(float, float, int, int, int, int)

    def __init__(self):
        super().__init__()
        self.ser = None
        self.running = False

    def start(self, port, baud):
        if self.running:
            self.stop()
        try:
            self.ser = serial.Serial(port, baud, timeout=1)
            self.running = True
            threading.Thread(target=self.read_loop, daemon=True).start()
        except Exception as e:
            print("Failed to open serial port.", e)

    def read_loop(self):
        while self.running:
            try:
                line = self.ser.readline().decode().strip()
                if not line:
                    continue
                parts = line.split(",")
                # Telemetry line from GCS: roll_error, pitch_error, m1, m2, m3, m4
                if len(parts) == 6:
                    r, p, m1, m2, m3, m4 = parts
                    self.data_received.emit(float(r), float(p),
                                            int(m1), int(m2), int(m3), int(m4))
            except:
                pass

    def stop(self):
        self.running = False
        try:
            if self.ser:
                self.ser.close()
        except:
            pass

    def send_line(self, s: str):
        if self.ser and self.ser.is_open:
            try:
                self.ser.write((s + "\n").encode())
            except Exception as e:
                print("Failed to send:", e)

# ---- GUI ----
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drone GCS GUI")

        self.layout = QVBoxLayout(self)

        # --- Serial controls ---
        serial_layout = QHBoxLayout()
        self.com_label = QLabel("COM:")
        self.com_selector = QComboBox()
        self.refresh_ports()
        self.baud_label = QLabel("Baud:")
        self.baud_selector = QComboBox()
        self.baud_selector.addItems(["9600","115200","230400"])
        serial_layout.addWidget(self.com_label)
        serial_layout.addWidget(self.com_selector)
        serial_layout.addWidget(self.baud_label)
        serial_layout.addWidget(self.baud_selector)
        self.layout.addLayout(serial_layout)

        # --- Control inputs ---
        grid = QGridLayout()
        grid.addWidget(QLabel("Axis:"), 0, 0)
        self.axis_cb = QComboBox(); self.axis_cb.addItems(["ROLL","PITCH"])
        grid.addWidget(self.axis_cb, 0, 1)

        grid.addWidget(QLabel("Desired (deg):"), 1, 0)
        self.setpoint_spin = QDoubleSpinBox(); self.setpoint_spin.setRange(-180,180); self.setpoint_spin.setSingleStep(0.1)
        grid.addWidget(self.setpoint_spin, 1, 1)

        grid.addWidget(QLabel("Kp:"), 2, 0)
        self.kp_spin = QDoubleSpinBox(); self.kp_spin.setRange(-10000,10000); self.kp_spin.setDecimals(2); self.kp_spin.setSingleStep(0.01)
        grid.addWidget(self.kp_spin, 2, 1)

        grid.addWidget(QLabel("Ki:"), 3, 0)
        self.ki_spin = QDoubleSpinBox(); self.ki_spin.setRange(-10000,10000); self.ki_spin.setDecimals(2); self.ki_spin.setSingleStep(0.01)
        grid.addWidget(self.ki_spin, 3, 1)

        grid.addWidget(QLabel("Kd:"), 4, 0)
        self.kd_spin = QDoubleSpinBox(); self.kd_spin.setRange(-10000,10000); self.kd_spin.setDecimals(2); self.kd_spin.setSingleStep(0.01)
        grid.addWidget(self.kd_spin, 4, 1)

        self.layout.addLayout(grid)

        # Roll/Pitch error plot
        self.error_plot = pg.PlotWidget(title="Roll & Pitch Error")
        self.error_plot.addLegend()
        self.curve_roll = self.error_plot.plot(pen='b', name="Roll error")
        self.curve_pitch = self.error_plot.plot(pen='g', name="Pitch error")
        self.stop_line_error = self.error_plot.addLine(y=0, pen=pg.mkPen('w', width=2))
        self.stop_line_error.setVisible(False)
        self.layout.addWidget(self.error_plot)

        # Motor PWM plot
        self.motor_plot = pg.PlotWidget(title="Motor PWMs")
        self.motor_plot.addLegend()
        self.curve_m1 = self.motor_plot.plot(pen='r', name="M1 [Front Right]")
        self.curve_m2 = self.motor_plot.plot(pen='g', name="M2 [Front Left]")
        self.curve_m3 = self.motor_plot.plot(pen='b', name="M3 [Rear Right]")
        self.curve_m4 = self.motor_plot.plot(pen='y', name="M4 [Rear Left]")
        self.stop_line_motor = self.motor_plot.addLine(y=0, pen=pg.mkPen('w', width=2))
        self.stop_line_motor.setVisible(False)
        self.layout.addWidget(self.motor_plot)

        # Buttons
        self.btn_start = QPushButton("START PROGRAM")
        self.btn_refresh_ports = QPushButton("Refresh COMs")
        hbtn = QHBoxLayout()
        hbtn.addWidget(self.btn_start)
        hbtn.addWidget(self.btn_refresh_ports)
        self.layout.addLayout(hbtn)

        # Data buffers
        self.xdata, self.roll_err, self.pitch_err = [], [], []
        self.m1, self.m2, self.m3, self.m4 = [], [], [], []
        self.t = 0
        self.plotting = False
        self.program_running = False  # indicates START sent and locked

        # Serial reader
        self.reader = SerialReader()
        self.reader.data_received.connect(self.update_data)

        # Log folder and file setup
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_folder = os.path.join(script_dir, "log")
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)
        dt_string = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(log_folder, f"drone_log_{dt_string}.csv")
        self.log_file = open(log_path, "w", newline="")
        self.logger = csv.writer(self.log_file)
        self.logger.writerow(["t","roll","pitch","M1","M2","M3","M4","event"])

        # Connect buttons
        self.btn_start.clicked.connect(self.toggle_start_stop)
        self.btn_refresh_ports.clicked.connect(self.refresh_ports)

    def refresh_ports(self):
        self.com_selector.clear()
        ports = serial.tools.list_ports.comports()
        for p in ports:
            self.com_selector.addItem(p.device)

    def start_serial(self):
        port = self.com_selector.currentText()
        baud = int(self.baud_selector.currentText())
        self.reader.start(port, baud)
        self.plotting = True
        self.stop_line_error.setVisible(False)
        self.stop_line_motor.setVisible(False)

    def stop_serial(self):
        self.reader.stop()
        self.plotting = False
        self.stop_line_error.setVisible(True)
        self.stop_line_motor.setVisible(True)

    def toggle_start_stop(self):
        # If serial not started yet, start it
        if not self.reader.running:
            self.start_serial()

        if not self.program_running:
            # send START command with parameters
            axis = self.axis_cb.currentText()
            setpoint = self.setpoint_spin.value()
            kp = self.kp_spin.value()
            ki = self.ki_spin.value()
            kd = self.kd_spin.value()
            cmd = f"START,{axis},{setpoint},{kp},{ki},{kd}"
            self.reader.send_line(cmd)
            # lock UI inputs
            self.axis_cb.setEnabled(False)
            self.setpoint_spin.setEnabled(False)
            self.kp_spin.setEnabled(False)
            self.ki_spin.setEnabled(False)
            self.kd_spin.setEnabled(False)
            self.btn_start.setText("STOP PROGRAM")
            self.program_running = True
            # log event
            self.t += 1
            self.logger.writerow([self.t, "","","","","","", "START"])
        else:
            # send STOP
            self.reader.send_line("STOP")
            # unlock UI inputs
            self.axis_cb.setEnabled(True)
            self.setpoint_spin.setEnabled(True)
            self.kp_spin.setEnabled(True)
            self.ki_spin.setEnabled(True)
            self.kd_spin.setEnabled(True)
            self.btn_start.setText("START PROGRAM")
            self.program_running = False
            # ensure motors stopped by logging STOP and writing an event row
            self.t += 1
            self.logger.writerow([self.t, "","","","","","", "STOP"])
            # Note: we keep serial connection open so user can start again without reselecting port.

    def update_data(self, r, p, m1, m2, m3, m4):
        MAX_POINTS = 200
        if not self.plotting:
            return

        self.t += 1
        self.xdata.append(self.t)
        self.roll_err.append(r)
        self.pitch_err.append(p)
        self.m1.append(m1)
        self.m2.append(m2)
        self.m3.append(m3)
        self.m4.append(m4)

        # log data
        self.logger.writerow([self.t,r,p,m1,m2,m3,m4, ""])

        # keep only last MAX_POINTS points
        if len(self.xdata) > MAX_POINTS:
            self.xdata = self.xdata[-MAX_POINTS:]
            self.roll_err = self.roll_err[-MAX_POINTS:]
            self.pitch_err = self.pitch_err[-MAX_POINTS:]
            self.m1 = self.m1[-MAX_POINTS:]
            self.m2 = self.m2[-MAX_POINTS:]
            self.m3 = self.m3[-MAX_POINTS:]
            self.m4 = self.m4[-MAX_POINTS:]

        # update plots
        self.curve_roll.setData(self.xdata, self.roll_err)
        self.curve_pitch.setData(self.xdata, self.pitch_err)
        self.curve_m1.setData(self.xdata, self.m1)
        self.curve_m2.setData(self.xdata, self.m2)
        self.curve_m3.setData(self.xdata, self.m3)
        self.curve_m4.setData(self.xdata, self.m4)

    def closeEvent(self, e):
        # On close, ensure program stopped and close serial/log
        if self.program_running:
            try:
                self.reader.send_line("STOP")
            except:
                pass
        self.reader.stop()
        self.log_file.close()
        e.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
