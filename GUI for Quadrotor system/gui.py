# Preamble
import sys
from dark_theme import dark_stylesheet
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTabWidget, QMainWindow, QComboBox, QPushButton, QGridLayout
)
import serial.tools.list_ports
from data import setup_timer

# Start App
app = QApplication(sys.argv)
app.setStyleSheet(dark_stylesheet)

window = QMainWindow()
window.setWindowTitle("QuadGCS")
window.setGeometry(100, 100, 800, 600)

# Create main tab widget
tabs = QTabWidget()
window.setCentralWidget(tabs)

# Add only one tab
data_tab = QWidget()
main_layout = QVBoxLayout()

## Top bar layout
top_bar = QHBoxLayout()
top_bar.addStretch()

### COM port dropdown
com_port_box = QComboBox()
ports = serial.tools.list_ports.comports()
for port in ports:
    com_port_box.addItem(port.device)
top_bar.addWidget(com_port_box)

### Baud rate dropdown
baud_rate_box = QComboBox()
baud_rate_box.addItems(["9600", "57600", "115200"])
top_bar.addWidget(baud_rate_box)

### Connect button
connect_button = QPushButton("CONNECT")
top_bar.addWidget(connect_button)

main_layout.addLayout(top_bar)

## Middle bar layout
middle_bar = QHBoxLayout()

### Left layout for RPY and Lat/Lon/Alt
left_layout = QGridLayout()

#### RPY labels
left_layout.addWidget(QLabel("Roll:"), 0, 0)
roll_label = QLabel("0.0")
left_layout.addWidget(roll_label, 0, 1)

left_layout.addWidget(QLabel("Pitch:"), 1, 0)
pitch_label = QLabel("0.0")
left_layout.addWidget(pitch_label, 1, 1)

left_layout.addWidget(QLabel("Yaw:"), 2, 0)
yaw_label = QLabel("0.0")
left_layout.addWidget(yaw_label, 2, 1)

#### Lat/Lon/Alt labels
left_layout.addWidget(QLabel("Latitude:"), 0, 2)
lat_label = QLabel("0.0")
left_layout.addWidget(lat_label, 0, 3)

left_layout.addWidget(QLabel("Longitude:"), 1, 2)
lon_label = QLabel("0.0")
left_layout.addWidget(lon_label, 1, 3)

left_layout.addWidget(QLabel("Altitude:"), 2, 2)
alt_label = QLabel("0.0")
left_layout.addWidget(alt_label, 2, 3)

middle_bar.addLayout(left_layout)
main_layout.addLayout(middle_bar)

data_tab.setLayout(main_layout)
tabs.addTab(data_tab, "Data")

# -----------------------------
# Set up live update timer
# -----------------------------
labels_dict = {
    'roll': roll_label,
    'pitch': pitch_label,
    'yaw': yaw_label,
    'lat': lat_label,
    'lon': lon_label,
    'alt': alt_label
}

setup_timer(labels_dict, com_port_box, baud_rate_box, app)

# Show GUI
window.show()
sys.exit(app.exec_())
