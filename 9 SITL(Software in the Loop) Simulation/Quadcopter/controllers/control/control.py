import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QGroupBox, QGridLayout, QComboBox, QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from dark_theme import dark_stylesheet

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from controller import Robot, InertialUnit, GPS

pwm_values = {
    'ch1': 1000, 'ch2': 1500, 'ch3': 1500,
    'ch4': 1500, 'ch5': 1000, 'ch6': 1000
}

gui_instance = None

class PWMHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global gui_instance
        parsed_url = self.path
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(parsed_url)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/connect":
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"OK")
            if gui_instance:
                gui_instance.signal_keepalive.emit()

        elif path == "/send_pwm":
            updated = {}
            for ch in pwm_values:
                if ch in query:
                    try:
                        val = int(float(query[ch][0]))
                        pwm_values[ch] = val
                        updated[ch] = val
                    except ValueError:
                        pass
            if gui_instance:
                gui_instance.signal_update.emit(updated)
                gui_instance.signal_keepalive.emit()

            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_error(404, "Not Found")

def run_http_server():
    server = HTTPServer(('0.0.0.0', 5000), PWMHandler)
    print("🚀 PWM HTTP Server running on port 5000...")
    server.serve_forever()

class LabeledProgressBar(QWidget):
    def __init__(self, name, ch, orientation=Qt.Vertical):
        super().__init__()
        self.ch = ch
        self.layout = QVBoxLayout() if orientation == Qt.Vertical else QHBoxLayout()
        self.label = QLabel(f"{name} ({ch.upper()})")
        self.progress = QProgressBar()
        self.value_label = QLabel(str(pwm_values[ch]))

        self.progress.setMinimum(1000)
        self.progress.setMaximum(2000)
        self.progress.setValue(pwm_values[ch])
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar::chunk { background-color: #007acc; }
            QProgressBar { border: 1px solid #444; text-align: center; }
        """)

        self.value_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label, alignment=Qt.AlignCenter)

        bar_layout = QVBoxLayout() if orientation == Qt.Vertical else QHBoxLayout()
        if orientation == Qt.Vertical:
            bar_layout.addWidget(self.value_label, alignment=Qt.AlignHCenter)
            bar_layout.addWidget(self.progress)
        else:
            bar_layout.addWidget(self.progress)
            bar_layout.addWidget(self.value_label)

        self.layout.addLayout(bar_layout)
        self.setLayout(self.layout)

    def update_value(self, value):
        self.progress.setValue(value)
        self.value_label.setText(str(value))

class MapCanvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure(facecolor='#121212')
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setStyleSheet("background-color: #121212;")
        self.path = []
        self.drone_dot, = self.ax.plot([], [], 'ro', markersize=8)
        self.path_line, = self.ax.plot([], [], color='purple', linewidth=2)
        self.ax.set_title("Map View", color='white')
        self.ax.set_xlabel("X", color='white')
        self.ax.set_ylabel("Y", color='white')
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.ax.grid(True, color='gray', linestyle='--', linewidth=0.5)
        self.ax.set_aspect('equal')

    def update_position(self, pos):
        self.path.append(pos)
        x_vals, y_vals = zip(*self.path)
        self.drone_dot.set_data([x_vals[-1]], [y_vals[-1]])
        self.path_line.set_data(x_vals, y_vals)
        self.ax.relim()
        self.ax.autoscale_view()
        self.draw()

class QuadcopterGUI(QWidget):
    signal_update = pyqtSignal(dict)
    signal_keepalive = pyqtSignal()

    def __init__(self):
        super().__init__()
        global gui_instance
        gui_instance = self

        self.setWindowTitle("Quadcopter GCS")
        self.setGeometry(200, 200, 1000, 750)
        self.setStyleSheet(dark_stylesheet)

        self.bars = {}
        self.connection_status = QLabel("Status: Not Connected")
        self.connection_status.setStyleSheet("color: red; font-weight: bold;")

        self.connection_timer = QTimer()
        self.connection_timer.setInterval(1000)
        self.connection_timer.setSingleShot(True)
        self.connection_timer.timeout.connect(self.mark_disconnected)

        self.signal_update.connect(self.update_gui)
        self.signal_keepalive.connect(self.mark_connected)

        self.init_ui()

    def init_ui(self):
        from PyQt5.QtWidgets import QPushButton, QCheckBox

        main_layout = QVBoxLayout()

        # Status + Simulation Button
        status_layout = QHBoxLayout()
        status_layout.addWidget(self.connection_status, alignment=Qt.AlignLeft)

        self.sim_button = QPushButton("Start Simulation")
        self.sim_button.setFixedWidth(200)
        self.sim_button.setStyleSheet("""
            QPushButton {
                color: lightgreen;
                background-color: #444444;
                font-weight: bold;
                border: 1px solid #888;
                padding: 5px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)
        self.sim_button.clicked.connect(lambda: print("Simulation Started"))

        self.reset_button = QPushButton("RESET")
        self.reset_button.setFixedWidth(150)
        self.reset_button.setStyleSheet("""
            QPushButton {
                color: orange;
                background-color: #444444;
                font-weight: bold;
                border: 1px solid #888;
                padding: 5px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.sim_button)
        btn_layout.addWidget(self.reset_button)
        status_layout.addLayout(btn_layout)
        main_layout.addLayout(status_layout)

        # Transmitter + Map
        transmitter_map_layout = QHBoxLayout()
        group = QGroupBox("Transmitter Values")
        grid = QGridLayout()

        def add_bar(name, ch, row, col, orientation, colspan=1):
            bar = LabeledProgressBar(name, ch, orientation)
            self.bars[ch] = bar
            grid.addWidget(bar, row, col, 1, colspan)

        add_bar("Yaw", "ch2", 0, 1, Qt.Horizontal)
        add_bar("Throttle", "ch1", 1, 0, Qt.Vertical)
        add_bar("Pitch", "ch4", 1, 2, Qt.Vertical)
        add_bar("Roll", "ch3", 2, 1, Qt.Horizontal)
        add_bar("CH5", "ch5", 3, 0, Qt.Horizontal, 3)
        add_bar("CH6", "ch6", 4, 0, Qt.Horizontal, 3)

        group.setLayout(grid)
        transmitter_map_layout.addWidget(group, stretch=1)
        self.map_canvas = MapCanvas()
        transmitter_map_layout.addWidget(self.map_canvas, stretch=1)
        main_layout.addLayout(transmitter_map_layout)

        # Flight Mode Selector
        mode_group = QGroupBox("Flight Mode Selector")
        mode_layout = QGridLayout()
        self.ch5_ranges = [(900, 1500), (1500, 2100)]
        self.ch6_ranges = [(900, 1300), (1300, 1700), (1700, 2100)]
        mode_options = ["Stabilize", "Alt Hold", "PosHold", "Land", "RTL", "No Mode"]
        self.mode_selectors = {'ch5': [], 'ch6': []}

        for i, (low, high) in enumerate(self.ch5_ranges):
            label = QLabel(f"CH5 ({low}-{high})")
            combo = QComboBox()
            combo.addItems(mode_options)
            combo.currentTextChanged.connect(lambda _, ch='ch5': self.update_active_mode(ch))
            self.mode_selectors['ch5'].append((combo, (low, high)))
            mode_layout.addWidget(label, i, 0)
            mode_layout.addWidget(combo, i, 1)

        for i, (low, high) in enumerate(self.ch6_ranges):
            label = QLabel(f"CH6 ({low}-{high})")
            combo = QComboBox()
            combo.addItems(mode_options)
            combo.currentTextChanged.connect(lambda _, ch='ch6': self.update_active_mode(ch))
            self.mode_selectors['ch6'].append((combo, (low, high)))
            mode_layout.addWidget(label, i, 2)
            mode_layout.addWidget(combo, i, 3)

        mode_group.setLayout(mode_layout)

        # PID Gains Tuner
        pid_group = QGroupBox("PID Gains Tuner")
        pid_layout = QGridLayout()
        pid_defaults = {
            'Throttle': (1.0, 0.5, 0.1),
            'Roll': (1.2, 0.6, 0.2),
            'Pitch': (1.2, 0.6, 0.2),
            'Yaw': (1.1, 0.4, 0.15),
        }
        self.pid_inputs = {}
        for row, (axis, (p, i, d)) in enumerate(pid_defaults.items()):
            axis_label = QLabel(f"{axis}:")
            p_label = QLabel("P:")
            i_label = QLabel("I:")
            d_label = QLabel("D:")
            p_value = QLineEdit(f"{p:.2f}")
            i_value = QLineEdit(f"{i:.2f}")
            d_value = QLineEdit(f"{d:.2f}")
            self.pid_inputs[axis] = {'P': p_value, 'I': i_value, 'D': d_value}
            pid_layout.addWidget(axis_label, row, 0)
            pid_layout.addWidget(p_label, row, 1)
            pid_layout.addWidget(p_value, row, 2)
            pid_layout.addWidget(i_label, row, 3)
            pid_layout.addWidget(i_value, row, 4)
            pid_layout.addWidget(d_label, row, 5)
            pid_layout.addWidget(d_value, row, 6)

        pid_group.setLayout(pid_layout)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(mode_group, 2)
        bottom_layout.addWidget(pid_group, 3)
        main_layout.addLayout(bottom_layout)

        # Failsafe Section
        failsafe_group = QGroupBox("Failsafe Configuration")
        failsafe_layout = QGridLayout()
        failsafe_options = ["No Mode", "Land", "RTL"]
        self.failsafe_dropdowns = {}

        def add_failsafe_row(label, row):
            failsafe_label = QLabel(label)
            combo = QComboBox()
            combo.addItems(failsafe_options)
            combo.setCurrentText("RTL")
            self.failsafe_dropdowns[label] = combo
            failsafe_layout.addWidget(failsafe_label, row, 0)
            failsafe_layout.addWidget(combo, row, 1)

        add_failsafe_row("Radio Failsafe:", 0)
        add_failsafe_row("Battery Failsafe:", 1)
        failsafe_group.setLayout(failsafe_layout)

        # Sensor Values Section
        sensor_group = QGroupBox("Sensor Values (Webots)")
        sensor_layout = QGridLayout()
        self.sensor_labels = {}

        orientation_labels = ["Roll (°)", "Pitch (°)", "Yaw (°)"]
        position_labels = ["X (m)", "Y (m)", "Altitude (m)"]

        for i, label_text in enumerate(orientation_labels):
            label = QLabel(label_text)
            value = QLabel("0.00")
            value.setStyleSheet("color: cyan; font-weight: bold;")
            self.sensor_labels[label_text] = value
            sensor_layout.addWidget(label, i, 0)
            sensor_layout.addWidget(value, i, 1)

        for i, label_text in enumerate(position_labels):
            label = QLabel(label_text)
            value = QLabel("0.00")
            value.setStyleSheet("color: lightgreen; font-weight: bold;")
            self.sensor_labels[label_text] = value
            sensor_layout.addWidget(label, i, 2)
            sensor_layout.addWidget(value, i, 3)

        sensor_group.setLayout(sensor_layout)

        failsafe_and_sensor_layout = QHBoxLayout()
        failsafe_and_sensor_layout.addWidget(failsafe_group, 1)
        failsafe_and_sensor_layout.addWidget(sensor_group, 1)
        main_layout.addLayout(failsafe_and_sensor_layout)

        # --- Parameters Group ---
        main_with_params_layout = QHBoxLayout()
        main_with_params_layout.addLayout(main_layout, stretch=5)

        parameters_group = QGroupBox("Parameters")
        parameters_group.setFixedWidth(350)
        parameters_layout = QVBoxLayout()

        # Limits Subgroup
        limits_group = QGroupBox("Limits")
        limits_layout = QGridLayout()
        limits_defaults = {
            "Max Roll Angle (°)": 45.0,
            "Max Pitch Angle (°)": 45.0,
            "Max Yaw Rate (°/s)": 180.0,
            "Max Climb Rate (m/s)": 5.0,
            "Max Descend Rate (m/s)": 3.0
        }
        self.limits_inputs = {}
        for i, (label_text, default_value) in enumerate(limits_defaults.items()):
            label = QLabel(label_text)
            input_field = QLineEdit(str(default_value))
            self.limits_inputs[label_text] = input_field
            limits_layout.addWidget(label, i, 0)
            limits_layout.addWidget(input_field, i, 1)
        limits_group.setLayout(limits_layout)

        # Complementary Filter & Sensors
        filter_group = QGroupBox("Complementary Filter & Sensors")
        filter_layout = QGridLayout()
        filter_defaults = {
            "Alpha Roll": 0.98,
            "Alpha Pitch": 0.98,
            "Alpha Yaw": 0.95,
            "Alpha Altitude": 0.90
        }
        self.filter_inputs = {}
        for i, (label_text, default_value) in enumerate(filter_defaults.items()):
            label = QLabel(label_text)
            input_field = QLineEdit(str(default_value))
            self.filter_inputs[label_text] = input_field
            filter_layout.addWidget(label, i, 0)
            filter_layout.addWidget(input_field, i, 1)
        gps_label = QLabel("Enable GPS")
        self.gps_checkbox = QCheckBox()
        self.gps_checkbox.setChecked(True)
        filter_layout.addWidget(gps_label, len(filter_defaults), 0)
        filter_layout.addWidget(self.gps_checkbox, len(filter_defaults), 1)
        filter_group.setLayout(filter_layout)

        # Mission Parameters
        mission_group = QGroupBox("Mission Parameters")
        mission_layout = QGridLayout()
        mission_defaults = {
            "Waypoint Radius (m)": 0.5,
            "RTL Altitude (m)": 10.0
        }
        self.mission_inputs = {}
        for i, (label_text, default_value) in enumerate(mission_defaults.items()):
            label = QLabel(label_text)
            input_field = QLineEdit(str(default_value))
            self.mission_inputs[label_text] = input_field
            mission_layout.addWidget(label, i, 0)
            mission_layout.addWidget(input_field, i, 1)
        mission_group.setLayout(mission_layout)

        # Power & PWM Settings
        power_group = QGroupBox("Power & PWM Settings")
        power_layout = QGridLayout()
        power_defaults = {
            "Voltage Threshold (V/cell)": 3.5,
            "Min PWM for Motors": 1000,
            "Max PWM for Motors": 2000
        }
        self.power_inputs = {}
        for i, (label_text, default_value) in enumerate(power_defaults.items()):
            label = QLabel(label_text)
            input_field = QLineEdit(str(default_value))
            self.power_inputs[label_text] = input_field
            power_layout.addWidget(label, i, 0)
            power_layout.addWidget(input_field, i, 1)
        power_group.setLayout(power_layout)

        # Add all to parameters layout
        parameters_layout.addWidget(limits_group)
        parameters_layout.addWidget(filter_group)
        parameters_layout.addWidget(mission_group)
        parameters_layout.addWidget(power_group)
        parameters_layout.addStretch()

        parameters_group.setLayout(parameters_layout)
        main_with_params_layout.addWidget(parameters_group, stretch=1)

        self.setLayout(main_with_params_layout)


    def update_active_mode(self, ch):
        val = pwm_values[ch]
        selectors = self.mode_selectors[ch]
        for combo, (low, high) in selectors:
            if low <= val <= high:
                combo.setStyleSheet("color: green; font-weight: bold;")
            else:
                combo.setStyleSheet("color: gray;")

    def mark_connected(self):
        self.connection_status.setText("Status: Connected to Transmitter")
        self.connection_status.setStyleSheet("color: green; font-weight: bold;")
        self.connection_timer.start()

    def mark_disconnected(self):
        self.connection_status.setText("Status: Not Connected")
        self.connection_status.setStyleSheet("color: red; font-weight: bold;")

    def update_gui(self, updates):
        for ch, val in updates.items():
            if ch in self.bars:
                self.bars[ch].update_value(val)
        self.update_active_mode("ch5")
        self.update_active_mode("ch6")

    def update_map(self, pos):
        self.map_canvas.update_position(pos)

    def update_sensor_values(self, roll, pitch, yaw, x, y, alt):
        self.sensor_labels["Roll (°)"].setText(f"{roll:.2f}")
        self.sensor_labels["Pitch (°)"].setText(f"{pitch:.2f}")
        self.sensor_labels["Yaw (°)"].setText(f"{yaw:.2f}")
        self.sensor_labels["X (m)"].setText(f"{x:.2f}")
        self.sensor_labels["Y (m)"].setText(f"{y:.2f}")
        self.sensor_labels["Altitude (m)"].setText(f"{alt:.2f}")

class WebotsSensorBridge:
    def __init__(self, gui):
        self.robot = Robot()
        self.time_step = int(self.robot.getBasicTimeStep())

        self.imu = self.robot.getDevice("inertial unit")
        self.gps = self.robot.getDevice("gps")

        self.imu.enable(self.time_step)
        self.gps.enable(self.time_step)

        self.gui = gui

        self.run_loop()

    def run_loop(self):
        import math
        while self.robot.step(self.time_step) != -1:
            rpy = self.imu.getRollPitchYaw()
            position = self.gps.getValues()

            roll = math.degrees(rpy[0])
            pitch = math.degrees(rpy[1])
            yaw = math.degrees(rpy[2])

            x = position[0]
            y = position[1]
            alt = position[2]

            self.gui.update_sensor_values(roll, pitch, yaw, x, y, alt)
            self.gui.update_map((x, y))

class Guidance:
    def __init__(self, gui):
        self.gui = gui

    def get_inputs(self):
        inputs = {
            'ch1': pwm_values['ch1'],  # Throttle
            'ch2': pwm_values['ch2'],  # Yaw
            'ch3': pwm_values['ch3'],  # Roll
            'ch4': pwm_values['ch4'],  # Pitch
            'ch5_mode': "No Mode",
            'ch6_mode': "No Mode",
            'limits': {},
            'mission': {},
            'power': {},
            'failsafe': {},
            'gps_enabled': self.gui.gps_checkbox.isChecked()
        }

        # Get CH5 mode
        ch5_val = pwm_values['ch5']
        for combo, (low, high) in self.gui.mode_selectors['ch5']:
            if low <= ch5_val <= high:
                inputs['ch5_mode'] = combo.currentText()
                break

        # Get CH6 mode
        ch6_val = pwm_values['ch6']
        for combo, (low, high) in self.gui.mode_selectors['ch6']:
            if low <= ch6_val <= high:
                inputs['ch6_mode'] = combo.currentText()
                break

        # Limits
        for label, field in self.gui.limits_inputs.items():
            inputs['limits'][label] = float(field.text())

        # Mission Parameters
        for label, field in self.gui.mission_inputs.items():
            inputs['mission'][label] = float(field.text())

        # Power Settings
        for label, field in self.gui.power_inputs.items():
            inputs['power'][label] = float(field.text())

        # Failsafe Options
        for label, dropdown in self.gui.failsafe_dropdowns.items():
            inputs['failsafe'][label] = dropdown.currentText()

        return inputs

if __name__ == "__main__":
    server_thread = threading.Thread(target=run_http_server, daemon=True)
    server_thread.start()

    app = QApplication(sys.argv)
    gui = QuadcopterGUI()
    gui.show()
    def start_guidance_loop():
        import time
        guidance = Guidance(gui_instance)
        while True:
            inputs = guidance.get_inputs()
            print(inputs)
            time.sleep(0.5)  # print every 0.5 seconds


    # Start Webots sensor reading in a thread
    def start_webots_bridge():
        WebotsSensorBridge(gui)

    threading.Thread(target=start_webots_bridge, daemon=True).start()
    threading.Thread(target=start_guidance_loop, daemon=True).start()

    sys.exit(app.exec_())
