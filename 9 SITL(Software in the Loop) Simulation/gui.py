import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QGroupBox, QGridLayout, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from dark_theme import dark_stylesheet

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Shared PWM values
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
        self.ax.set_title("XY Map", color='white')
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

        self.setWindowTitle("Quadcopter GUI")
        self.setGeometry(200, 200, 1250, 750)
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
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.connection_status, alignment=Qt.AlignLeft)

        # Transmitter + Map side-by-side
        transmitter_map_layout = QHBoxLayout()

        # Transmitter Group
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
        transmitter_map_layout.addWidget(group)

        # Map
        self.map_canvas = MapCanvas()
        transmitter_map_layout.addWidget(self.map_canvas)
        self.map_canvas.setFixedHeight(group.sizeHint().height())

        main_layout.addLayout(transmitter_map_layout)

        # Flight Mode
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
        main_layout.addWidget(mode_group)

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
        main_layout.addWidget(failsafe_group)

        self.setLayout(main_layout)

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


if __name__ == "__main__":
    server_thread = threading.Thread(target=run_http_server, daemon=True)
    server_thread.start()

    app = QApplication(sys.argv)
    gui = QuadcopterGUI()
    gui.show()

    # Example simulation of Webots input
    def simulate_position():
        import time
        for i in range(100):
            gui.update_map((i, i * 0.5))
            time.sleep(0.1)

    threading.Thread(target=simulate_position, daemon=True).start()

    sys.exit(app.exec_())
