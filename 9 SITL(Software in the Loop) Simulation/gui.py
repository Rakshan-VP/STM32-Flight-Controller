import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QGroupBox, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
import urllib.parse
import threading
from dark_theme import dark_stylesheet

# Shared PWM values
pwm_values = {
    'ch1': 1000, 'ch2': 1500, 'ch3': 1500,
    'ch4': 1500, 'ch5': 1000, 'ch6': 1000
}

gui_instance = None

class PWMHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global gui_instance
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

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
                        val = int(float(query[ch][0]))  # float to int to handle decimal PWM
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
        self.orientation = orientation

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

        if orientation == Qt.Vertical:
            bar_layout = QVBoxLayout()
            bar_layout.addWidget(self.value_label, alignment=Qt.AlignHCenter)
            bar_layout.addWidget(self.progress)
            self.layout.addLayout(bar_layout)
        else:
            bar_layout = QHBoxLayout()
            bar_layout.addWidget(self.progress)
            bar_layout.addWidget(self.value_label)
            self.layout.addLayout(bar_layout)

        self.setLayout(self.layout)

    def update_value(self, value):
        self.progress.setValue(value)
        self.value_label.setText(str(value))


class QuadcopterGUI(QWidget):
    signal_update = pyqtSignal(dict)
    signal_keepalive = pyqtSignal()  # NEW SIGNAL

    def __init__(self):
        super().__init__()
        global gui_instance
        gui_instance = self

        self.setWindowTitle("Quadcopter GUI")
        self.setGeometry(200, 200, 600, 500)
        self.setStyleSheet(dark_stylesheet)

        self.bars = {}
        self.connection_status = QLabel("Status: Not Connected")
        self.connection_status.setStyleSheet("color: red; font-weight: bold;")

        self.connection_timer = QTimer()
        self.connection_timer.setInterval(1000)  
        self.connection_timer.setSingleShot(True)
        self.connection_timer.timeout.connect(self.mark_disconnected)

        self.signal_update.connect(self.update_gui)
        self.signal_keepalive.connect(self.mark_connected)  # Connect the signal

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        main_layout.addWidget(self.connection_status, alignment=Qt.AlignLeft)

        group = QGroupBox("Transmitter Values")
        grid = QGridLayout()

        def add_bar(name, ch, row, col, orientation, colspan=1):
            bar = LabeledProgressBar(name, ch, orientation)
            self.bars[ch] = bar
            grid.addWidget(bar, row, col, 1, colspan)

        # Square layout for transmitter
        add_bar("Yaw", "ch2", 0, 1, Qt.Horizontal)
        add_bar("Throttle", "ch1", 1, 0, Qt.Vertical)
        add_bar("Pitch", "ch4", 1, 2, Qt.Vertical)
        add_bar("Roll", "ch3", 2, 1, Qt.Horizontal)
        add_bar("CH5", "ch5", 3, 0, Qt.Horizontal, 3)
        add_bar("CH6", "ch6", 4, 0, Qt.Horizontal, 3)

        group.setLayout(grid)
        main_layout.addWidget(group)

        self.setLayout(main_layout)

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


if __name__ == "__main__":
    server_thread = threading.Thread(target=run_http_server, daemon=True)
    server_thread.start()

    app = QApplication(sys.argv)
    gui = QuadcopterGUI()
    gui.show()
    sys.exit(app.exec_())
