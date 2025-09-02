import sys
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QGroupBox, QGridLayout, QComboBox, QLineEdit, QPushButton, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from dark_theme import dark_stylesheet
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from controller import Robot

# --- Globals ---
pwm_values = {f'ch{i}': 1500 for i in range(1, 7)}
pwm_values.update({'ch1': 1000, 'ch5': 1000, 'ch6': 1000})
pwm_lock = threading.Lock()
gui_instance = None

# --- Utility Functions ---
def parse_pwm_update(query):
    with pwm_lock:
        return {ch: int(float(query[ch][0]))
                for ch in pwm_values if ch in query and query[ch][0].replace('.', '', 1).isdigit()}

def map_pwm(pwm, max_val):
    return (pwm - 1500) / 500 * max_val

def clamp(val, minv, maxv):
    return max(min(val, maxv), minv)

# --- HTTP PWM Handler ---
class PWMHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global gui_instance
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/connect":
            self._send_ok()
            if gui_instance:
                gui_instance.signal_keepalive.emit()
        elif path == "/send_pwm":
            updated = parse_pwm_update(query)
            pwm_values.update(updated)
            if gui_instance:
                gui_instance.signal_update.emit(updated)
                gui_instance.signal_keepalive.emit()
            self._send_ok()

    def _send_ok(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"OK")

def run_http_server():
    server = HTTPServer(('0.0.0.0', 5000), PWMHandler)
    print("🚀 PWM HTTP Server running on port 5000...")
    server.serve_forever()

# --- UI Widgets ---
class LabeledProgressBar(QWidget):
    def __init__(self, name, ch, orientation=Qt.Vertical):
        super().__init__()
        self.ch = ch
        self.progress = QProgressBar()
        self.value_label = QLabel(str(pwm_values[self.ch]))
        self._init_ui(name, orientation)

    def _init_ui(self, name, orientation):
        layout = QVBoxLayout() if orientation == Qt.Vertical else QHBoxLayout()
        label = QLabel(f"{name} ({self.ch.upper()})")
        self.progress.setRange(1000, 2000)
        self.progress.setValue(pwm_values[self.ch])
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(
            "QProgressBar::chunk { background-color: #007acc; }"
            "QProgressBar { border: 1px solid #444; text-align: center; }"
        )
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label, alignment=Qt.AlignCenter)
        widgets = [self.value_label, self.progress] if orientation == Qt.Vertical else [self.progress, self.value_label]
        for w in widgets:
            layout.addWidget(w)
        self.setLayout(layout)

    def update_value(self, value):
        self.progress.setValue(value)
        self.value_label.setText(str(value))

class MapCanvas(FigureCanvas):
    def __init__(self):
        fig = Figure(facecolor='#121212')
        self.ax = fig.add_subplot(111)
        super().__init__(fig)
        self.setStyleSheet("background-color: #121212;")
        self.drone_dot, = self.ax.plot([], [], 'ro', markersize=8)
        self.path_line, = self.ax.plot([], [], color='purple', linewidth=2)
        self.path = []
        self._init_axes()

    def _init_axes(self):
        ax = self.ax
        ax.set_title("Map View", color='white')
        ax.set_xlabel("X", color='white')
        ax.set_ylabel("Y", color='white')
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        ax.grid(True, color='gray', linestyle='--', linewidth=0.5)
        ax.set_aspect('equal')

    def update_position(self, pos):
        self.path.append(pos)
        x_vals, y_vals = zip(*self.path) if self.path else ([], [])
        self.drone_dot.set_data([x_vals[-1]], [y_vals[-1]])
        self.path_line.set_data(x_vals, y_vals)
        self.ax.relim()
        self.ax.autoscale_view()
        self.draw()

# --- Main GUI Widget ---
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
        self.mode_selectors = {'ch5': [], 'ch6': []}
        self._init_signals()
        self._build_ui()

    def _init_signals(self):
        self.connection_status = QLabel("Status: Not Connected")
        self.connection_status.setStyleSheet("color: red; font-weight: bold;")
        self.connection_timer = QTimer()
        self.connection_timer.setInterval(1000)
        self.connection_timer.setSingleShot(True)
        self.connection_timer.timeout.connect(self.mark_disconnected)
        self.signal_update.connect(self.update_gui)
        self.signal_keepalive.connect(self.mark_connected)

    def _build_ui(self):
        main_layout = QVBoxLayout()
        main_layout.addLayout(self._top_status_buttons())
        main_layout.addLayout(self._transmitter_and_map_layout())
        main_layout.addLayout(self._bottom_layout())
        main_layout.addLayout(self._failsafe_and_sensor_layout())
        main_with_params_layout = QHBoxLayout()
        main_with_params_layout.addLayout(main_layout, stretch=5)
        main_with_params_layout.addWidget(self._parameters_group(), stretch=1)
        self.setLayout(main_with_params_layout)

    def _top_status_buttons(self):
        layout = QHBoxLayout()
        layout.addWidget(self.connection_status, alignment=Qt.AlignLeft)
        sim_btn = self._make_button("Start Simulation", "lightgreen")
        reset_btn = self._make_button("RESET", "orange", width=150)
        layout.addWidget(sim_btn)
        layout.addWidget(reset_btn)
        return layout

    def _make_button(self, label, color, width=200):
        btn = QPushButton(label)
        btn.setFixedWidth(width)
        btn.setStyleSheet(
            f"QPushButton {{ color: {color}; background-color: #444; font-weight: bold; "
            "border: 1px solid #888; padding: 5px; border-radius: 4px;}}"
            "QPushButton:hover { background-color: #555; }"
        )
        btn.clicked.connect(lambda: print(f"{label} clicked"))
        return btn

    def _transmitter_and_map_layout(self):
        layout = QHBoxLayout()
        tx_group = QGroupBox("Transmitter Values")
        grid = QGridLayout()
        self._add_bar("Yaw", "ch2", grid, 0, 1, Qt.Horizontal)
        self._add_bar("Throttle", "ch1", grid, 1, 0, Qt.Vertical)
        self._add_bar("Pitch", "ch4", grid, 1, 2, Qt.Vertical)
        self._add_bar("Roll", "ch3", grid, 2, 1, Qt.Horizontal)
        self._add_bar("CH5", "ch5", grid, 3, 0, Qt.Horizontal, 3)
        self._add_bar("CH6", "ch6", grid, 4, 0, Qt.Horizontal, 3)
        tx_group.setLayout(grid)
        layout.addWidget(tx_group, stretch=1)
        self.map_canvas = MapCanvas()
        layout.addWidget(self.map_canvas, stretch=1)
        return layout

    def _add_bar(self, name, ch, grid, row, col, orientation, colspan=1):
        bar = LabeledProgressBar(name, ch, orientation)
        self.bars[ch] = bar
        grid.addWidget(bar, row, col, 1, colspan)

    def _bottom_layout(self):
        layout = QHBoxLayout()
        layout.addWidget(self._mode_group(), 2)
        layout.addWidget(self._pid_group(), 3)
        return layout

    def _mode_group(self):
        group = QGroupBox("Flight Mode Selector")
        grid = QGridLayout()
        def add_mode_selector(channel, ranges, options, col_offset=0):
            for i, (low, high) in enumerate(ranges):
                combo = QComboBox()
                combo.addItems(options)
                combo.currentTextChanged.connect(lambda _, c=channel: self.update_active_mode(c))
                self.mode_selectors[channel].append((combo, (low, high)))
                grid.addWidget(QLabel(f"{channel.upper()} ({low}-{high})"), i, col_offset)
                grid.addWidget(combo, i, col_offset+1)

        add_mode_selector('ch5', [(900, 1500), (1500, 2100)], ["No Mode", "RTL", "Land"], 0)
        add_mode_selector('ch6', [(900, 1300), (1300, 1700), (1700, 2100)],
                          ["Stabilize", "Alt Hold", "PosHold", "Land", "RTL", "No Mode"], 2)
        group.setLayout(grid)
        return group

    def _pid_group(self):
        group = QGroupBox("PID Gains Tuner")
        grid = QGridLayout()
        pid_defaults = {
            'Throttle': (1.0, 0.5, 0.1), 'Roll': (1.2, 0.6, 0.2),
            'Pitch': (1.2, 0.6, 0.2), 'Yaw': (1.1, 0.4, 0.15)
        }
        self.pid_inputs = {}
        for row, (axis, (p, i, d)) in enumerate(pid_defaults.items()):
            self.pid_inputs[axis] = {k: QLineEdit(f"{v:.2f}") for k, v in zip('PID', (p, i, d))}
            grid.addWidget(QLabel(f"{axis}:"), row, 0)
            for j, k in enumerate('PID'):
                grid.addWidget(QLabel(f"{k}:"), row, 1+2*j)
                grid.addWidget(self.pid_inputs[axis][k], row, 2+2*j)
        group.setLayout(grid)
        return group

    def _failsafe_and_sensor_layout(self):
        failsafe_group = self._dropdown_group("Failsafe Configuration", ["Radio Failsafe:", "Battery Failsafe:"],
                                              ["No Mode", "Land", "RTL"], combo_style={"RTL": True})
        sensor_group = self._sensor_group()
        layout = QHBoxLayout()
        layout.addWidget(failsafe_group, 1)
        layout.addWidget(sensor_group, 1)
        return layout

    def _dropdown_group(self, group_title, labels, options, combo_style=None):
        group = QGroupBox(group_title)
        grid = QGridLayout()
        self.failsafe_dropdowns = {}
        for i, label in enumerate(labels):
            combo = QComboBox()
            combo.addItems(options)
            combo.setCurrentText(options[1] if combo_style and "RTL" in options else options[0])
            self.failsafe_dropdowns[label] = combo
            grid.addWidget(QLabel(label), i, 0)
            grid.addWidget(combo, i, 1)
        group.setLayout(grid)
        return group

    def _sensor_group(self):
        group = QGroupBox("Sensor Values (Webots)")
        grid = QGridLayout()
        self.sensor_labels = {}
        for i, label_text in enumerate(["Roll (°)", "Pitch (°)", "Yaw (°)"]):
            value = QLabel("0.00")
            value.setStyleSheet("color: cyan; font-weight: bold;")
            self.sensor_labels[label_text] = value
            grid.addWidget(QLabel(label_text), i, 0)
            grid.addWidget(value, i, 1)
        for i, label_text in enumerate(["X (m)", "Y (m)", "Altitude (m)"]):
            value = QLabel("0.00")
            value.setStyleSheet("color: lightgreen; font-weight: bold;")
            self.sensor_labels[label_text] = value
            grid.addWidget(QLabel(label_text), i, 2)
            grid.addWidget(value, i, 3)
        group.setLayout(grid)
        return group

    def _parameters_group(self):
        group = QGroupBox("Parameters")
        group.setFixedWidth(350)
        layout = QVBoxLayout()
        self.limits_inputs = self._make_param_inputs(layout, "Limits", {
            "Max Roll Angle (°)": 45.0, "Max Pitch Angle (°)": 45.0,
            "Max Yaw Rate (°/s)": 180.0, "Max Climb Rate (m/s)": 5.0,
            "Max Descend Rate (m/s)": 3.0})
        self.filter_inputs = self._make_param_inputs(layout, "Complementary Filter & Sensors", {
            "Alpha Roll": 0.98, "Alpha Pitch": 0.98, "Alpha Yaw": 0.95, "Alpha Altitude": 0.90}, gps_field=True)
        self.mission_inputs = self._make_param_inputs(layout, "Mission Parameters", {
            "Waypoint Radius (m)": 0.5, "RTL Altitude (m)": 10.0})
        self.power_inputs = self._make_param_inputs(layout, "Power & PWM Settings", {
            "Voltage Threshold (V/cell)": 3.5, "Min PWM for Motors": 1000, "Max PWM for Motors": 2000})
        layout.addStretch()
        group.setLayout(layout)
        return group

    def _make_param_inputs(self, parent_layout, group_title, defaults, gps_field=False):
        group = QGroupBox(group_title)
        grid = QGridLayout()
        inputs = {}
        for i, (label, default) in enumerate(defaults.items()):
            field = QLineEdit(str(default))
            inputs[label] = field
            grid.addWidget(QLabel(label), i, 0)
            grid.addWidget(field, i, 1)
        if gps_field:
            gps_cb = QCheckBox()
            gps_cb.setChecked(True)
            self.gps_checkbox = gps_cb
            grid.addWidget(QLabel("Enable GPS"), len(defaults), 0)
            grid.addWidget(gps_cb, len(defaults), 1)
        group.setLayout(grid)
        parent_layout.addWidget(group)
        return inputs

    def update_active_mode(self, ch):
        val = pwm_values[ch]
        for combo, (low, high) in self.mode_selectors[ch]:
            combo.setStyleSheet("color: green; font-weight: bold;" if low <= val <= high else "color: gray;")

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
        update = {
            "Roll (°)": roll, "Pitch (°)": pitch, "Yaw (°)": yaw,
            "X (m)": x, "Y (m)": y, "Altitude (m)": alt
        }
        for k, v in update.items():
            self.sensor_labels[k].setText(f"{v:.2f}")

# --- Core Guidance Logic ---
class Guidance:
    def __init__(self, gui):
        self.gui = gui
        self.robot = Robot()
        self.time_step = int(self.robot.getBasicTimeStep())
        self.imu = self.robot.getDevice("inertial unit")
        self.gps = self.robot.getDevice("gps")
        self.imu.enable(self.time_step)
        self.gps.enable(self.time_step)
        self.des_x = self.des_y = 0
        self.home_x = self.home_y = self.home_alt = None
        self.reached_home = False

    def get_sensor_readings(self):
        import math
        self.robot.step(self.time_step)
        rpy = self.imu.getRollPitchYaw()
        position = self.gps.getValues()
        roll, pitch, yaw = map(math.degrees, rpy)
        x, y, alt = position
        self.gui.update_sensor_values(roll, pitch, yaw, x, y, alt)
        self.gui.update_map((x, y))
        return roll, pitch, yaw, x, y, alt

    def get_inputs(self):
        import math
        roll, pitch, yaw, x, y, alt = self.get_sensor_readings()
        dt = self.time_step / 1000.0
        yaw_rad = math.radians(yaw)
        limits = {k: float(v.text()) for k, v in self.gui.limits_inputs.items()}
        mission = {k: float(v.text()) for k, v in self.gui.mission_inputs.items()}
        power = {k: float(v.text()) for k, v in self.gui.power_inputs.items()}

        def get_mode(channel):
            val = pwm_values[channel]
            for combo, (low, high) in self.gui.mode_selectors[channel]:
                if low <= val <= high:
                    return combo.currentText()
            return "No Mode"

        mode5, mode6 = get_mode('ch5'), get_mode('ch6')
        ch1, ch2, ch3, ch4 = [pwm_values[f'ch{i}'] for i in range(1, 5)]
        rtl_height, wp_radius = mission["RTL Altitude (m)"], mission["Waypoint Radius (m)"]

        if self.home_x is None:
            self.home_x, self.home_y, self.home_alt = x, y, alt

        # --- MODES ---
        if mode5 == "No Mode":
            if mode6 == "Stabilize" or mode6 == "Alt Hold":
                roll_error = map_pwm(ch3, limits["Max Roll Angle (°)"]) - roll
                pitch_error = map_pwm(ch4, limits["Max Pitch Angle (°)"]) - pitch
                yaw_rate_err = map_pwm(ch2, limits["Max Yaw Rate (°/s)"])
                if mode6 == "Stabilize":
                    return {'mode': 'Stabilize', 'throttle_pwm': ch1, 'yaw_rate_error': yaw_rate_err,
                            'roll_error': roll_error, 'pitch_error': pitch_error}
                if mode6 == "Alt Hold":
                    des_alt = (alt + ((ch1-1500)/500)*limits["Max Climb Rate (m/s)"]*dt) if ch1 != 1500 else alt
                    alt_error = des_alt - alt
                    return {'mode': 'Alt Hold', 'yaw_rate_error': yaw_rate_err,
                            'roll_error': roll_error, 'pitch_error': pitch_error, 'alt_error': alt_error}

            elif mode6 == "PosHold":
                des_alt = (alt + ((ch1-1500)/500)*limits["Max Climb Rate (m/s)"]*dt) if ch1 > 1500 else (
                          alt - ((1500-ch1)/500)*limits["Max Descend Rate (m/s)"]*dt) if ch1 < 1500 else alt
                alt_error = des_alt - alt
                if ch3 == ch4 == 1500:
                    self.des_x, self.des_y = x, y
                x_err, y_err = self.des_x - x, self.des_y - y
                x_body = x_err * math.cos(yaw_rad) + y_err * math.sin(yaw_rad)
                y_body = -x_err * math.sin(yaw_rad) + y_err * math.cos(yaw_rad)
                des_roll = clamp(x_body, -limits["Max Roll Angle (°)"], limits["Max Roll Angle (°)"])
                des_pitch = clamp(y_body, -limits["Max Pitch Angle (°)"], limits["Max Pitch Angle (°)"])
                if ch3 != 1500: des_roll = map_pwm(ch3, limits["Max Roll Angle (°)"])
                if ch4 != 1500: des_pitch = map_pwm(ch4, limits["Max Pitch Angle (°)"])
                des_yaw_rate = map_pwm(ch2, limits["Max Yaw Rate (°/s)"])
                return {'mode': 'PosHold', 'yaw_rate_error': des_yaw_rate,
                        'roll_error': des_roll-roll, 'pitch_error': des_pitch-pitch, 'alt_error': alt_error}

        if mode5 == "Land":
            if not (self.des_x or self.des_y):
                self.des_x, self.des_y = x, y
            x_err, y_err = self.des_x - x, self.des_y - y
            x_body = x_err * math.cos(yaw_rad) + y_err * math.sin(yaw_rad)
            y_body = -x_err * math.sin(yaw_rad) + y_err * math.cos(yaw_rad)
            des_roll = clamp(x_body, -limits["Max Roll Angle (°)"], limits["Max Roll Angle (°)"])
            des_pitch = clamp(y_body, -limits["Max Pitch Angle (°)"], limits["Max Pitch Angle (°)"])
            alt_error = -alt
            return {'mode': 'Land', 'yaw_rate_error': 0,
                    'roll_error': des_roll - roll, 'pitch_error': des_pitch - pitch,
                    'alt_error': alt_error, 'land_complete': abs(alt_error) < 0.3}

        if mode5 == "RTL":
            x_err, y_err = self.home_x - x, self.home_y - y
            xy_dist = math.hypot(x_err, y_err)
            if not self.reached_home and xy_dist <= wp_radius:
                self.reached_home = True
            if not self.reached_home:
                x_body = x_err * math.cos(yaw_rad) + y_err * math.sin(yaw_rad)
                y_body = -x_err * math.sin(yaw_rad) + y_err * math.cos(yaw_rad)
                des_roll = clamp(x_body, -limits["Max Roll Angle (°)"], limits["Max Roll Angle (°)"])
                des_pitch = clamp(y_body, -limits["Max Pitch Angle (°)"], limits["Max Pitch Angle (°)"])
                alt_error = rtl_height - alt
                return {'mode': 'RTL', 'yaw_rate_error': 0,
                        'roll_error': des_roll - roll, 'pitch_error': des_pitch - pitch,
                        'alt_error': alt_error}
            else:
                x_body = x_err * math.cos(yaw_rad) + y_err * math.sin(yaw_rad)
                y_body = -x_err * math.sin(yaw_rad) + y_err * math.cos(yaw_rad)
                des_roll = clamp(x_body, -limits["Max Roll Angle (°)"], limits["Max Roll Angle (°)"])
                des_pitch = clamp(y_body, -limits["Max Pitch Angle (°)"], limits["Max Pitch Angle (°)"])
                alt_error = -alt
                return {'mode': 'RTL-Landing', 'yaw_rate_error': 0,
                        'roll_error': des_roll - roll, 'pitch_error': des_pitch - pitch,
                        'alt_error': alt_error, 'land_complete': abs(alt_error) < 0.3}
        # fallback
        return {
            'ch1': pwm_values['ch1'], 'ch2': pwm_values['ch2'], 'ch3': pwm_values['ch3'], 'ch4': pwm_values['ch4'],
            'ch5_mode': mode5, 'ch6_mode': mode6,
            'limits': limits, 'mission': mission, 'power': power,
            'failsafe': {k: v.currentText() for k, v in self.gui.failsafe_dropdowns.items()},
            'gps_enabled': getattr(self.gui, "gps_checkbox", None) and self.gui.gps_checkbox.isChecked(),
            'sensor': {'roll': roll, 'pitch': pitch, 'yaw': yaw, 'x': x, 'y': y, 'altitude': alt}
        }

class PID:
    def __init__(self, kp, ki, kd):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.integral = 0
        self.prev_error = 0

    def compute(self, error, dt):
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt if dt > 0 else 0
        self.prev_error = error
        return self.kp * error + self.ki * self.integral + self.kd * derivative
    
class Control:
    def __init__(self, gui, robot):
        self.gui = gui
        self.robot = robot
        self.dt = robot.getBasicTimeStep() / 1000.0
        self.motors = {
            'm1': robot.getDevice("m1"),
            'm2': robot.getDevice("m2"),
            'm3': robot.getDevice("m3"),
            'm4': robot.getDevice("m4")
        }
        for m in self.motors.values():
            m.setPosition(float('inf'))
            m.setVelocity(0)

        self.max_velocity = 100
        self._init_pids()

    def _init_pids(self):
        self.pid = {}
        for axis in ['Throttle', 'Roll', 'Pitch', 'Yaw']:
            kp = float(self.gui.pid_inputs[axis]['P'].text())
            ki = float(self.gui.pid_inputs[axis]['I'].text())
            kd = float(self.gui.pid_inputs[axis]['D'].text())
            self.pid[axis.lower()] = PID(kp, ki, kd)

    def apply_control(self, inputs):
        mode = inputs.get('mode')
        if mode not in ['Stabilize', 'Alt Hold', 'PosHold', 'Land', 'RTL', 'RTL-Landing']:
            self._stop_motors()
            return

        # Re-initialize PID values every loop to reflect real-time GUI updates
        self._init_pids()

        roll_c = self.pid['roll'].compute(inputs['roll_error'], self.dt)
        pitch_c = self.pid['pitch'].compute(inputs['pitch_error'], self.dt)
        yaw_c = self.pid['yaw'].compute(inputs['yaw_rate_error'], self.dt)
        alt_c = self.pid['throttle'].compute(inputs.get('alt_error', 0), self.dt)

        # --- Motor Mixing (X configuration)
        m1 = alt_c - roll_c + pitch_c + yaw_c  # Front Left
        m2 = alt_c + roll_c + pitch_c - yaw_c  # Front Right
        m3 = alt_c + roll_c - pitch_c + yaw_c  # Back Right
        m4 = alt_c - roll_c - pitch_c - yaw_c  # Back Left

        velocities = [m1, m2, m3, m4]
        velocities = self._normalize_and_scale(velocities)

        for i, key in enumerate(['m1', 'm2', 'm3', 'm4']):
            self.motors[key].setVelocity(velocities[i])

    def _normalize_and_scale(self, vals):
        min_val = min(vals)
        vals = [v - min_val for v in vals]  # shift to 0 base
        max_val = max(vals)
        if max_val == 0:
            return [0] * len(vals)
        return [clamp(v / max_val * self.max_velocity, 0, self.max_velocity) for v in vals]

    def _stop_motors(self):
        for m in self.motors.values():
            m.setVelocity(0)

# --- Main Execution ---
if __name__ == "__main__":
    threading.Thread(target=run_http_server, daemon=True).start()
    app = QApplication(sys.argv)
    gui = QuadcopterGUI()
    gui.show()

    def start_guidance_loop():
        guidance = Guidance(gui_instance)
        control = Control(gui_instance, guidance.robot)
        while True:
            inputs = guidance.get_inputs()
            control.apply_control(inputs)
            time.sleep(0.005)

    threading.Thread(target=start_guidance_loop, daemon=True).start()
    sys.exit(app.exec_())
