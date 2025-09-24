# gui.py
import sys
import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTabWidget, QMainWindow, QComboBox, QPushButton, QGridLayout
)
from dark_theme import dark_stylesheet
from data import setup_timer, create_map_widget


def create_data_tab():
    """Create the Data tab layout and return tab widget, labels, and update_map function."""
    data_tab = QWidget()
    main_layout = QVBoxLayout()

    # -----------------------
    # Top bar layout
    # -----------------------
    top_bar = QHBoxLayout()
    top_bar.addStretch()

    # COM port dropdown
    com_port_box = QComboBox()
    ports = serial.tools.list_ports.comports()
    for port in ports:
        com_port_box.addItem(port.device)
    top_bar.addWidget(com_port_box)

    # Baud rate dropdown
    baud_rate_box = QComboBox()
    baud_rate_box.addItems(["9600", "57600", "115200"])
    top_bar.addWidget(baud_rate_box)

    # Connect button
    connect_button = QPushButton("CONNECT")
    top_bar.addWidget(connect_button)

    main_layout.addLayout(top_bar)

    # -----------------------
    # Middle bar layout
    # -----------------------
    middle_bar = QHBoxLayout()

    # Left layout for RPY and Lat/Lon/Alt
    left_layout = QGridLayout()

    # RPY labels
    roll_label = QLabel("0.0")
    pitch_label = QLabel("0.0")
    yaw_label = QLabel("0.0")

    left_layout.addWidget(QLabel("Roll:"), 0, 0)
    left_layout.addWidget(roll_label, 0, 1)
    left_layout.addWidget(QLabel("Pitch:"), 1, 0)
    left_layout.addWidget(pitch_label, 1, 1)
    left_layout.addWidget(QLabel("Yaw:"), 2, 0)
    left_layout.addWidget(yaw_label, 2, 1)

    # Lat/Lon/Alt labels
    lat_label = QLabel("0.0")
    lon_label = QLabel("0.0")
    alt_label = QLabel("0.0")

    left_layout.addWidget(QLabel("Latitude:"), 0, 2)
    left_layout.addWidget(lat_label, 0, 3)
    left_layout.addWidget(QLabel("Longitude:"), 1, 2)
    left_layout.addWidget(lon_label, 1, 3)
    left_layout.addWidget(QLabel("Altitude:"), 2, 2)
    left_layout.addWidget(alt_label, 2, 3)

    middle_bar.addLayout(left_layout)

    # -----------------------
    # Right layout for Map + Status labels (map on top, labels in one row below)
    # -----------------------
    right_layout = QVBoxLayout()

    # Map widget (top)
    map_widget, update_map = create_map_widget()
    right_layout.addWidget(map_widget)

    # Status labels (below map in a single horizontal row)
    status_layout = QHBoxLayout()
    flight_mode_label = QLabel("Flight Mode: ---")
    armed_label = QLabel("Armed: ---")
    imu_label = QLabel("IMU: ---")
    gps_label = QLabel("GPS: ---")
    battery_label = QLabel("Battery: ---")

    status_layout.addWidget(flight_mode_label)
    status_layout.addWidget(armed_label)
    status_layout.addWidget(imu_label)
    status_layout.addWidget(gps_label)
    status_layout.addWidget(battery_label)
    status_layout.addStretch()  # push labels to left

    right_layout.addLayout(status_layout)

    middle_bar.addLayout(right_layout)

    main_layout.addLayout(middle_bar)
    data_tab.setLayout(main_layout)

    # Pack labels into dict
    labels_dict = {
        'roll': roll_label,
        'pitch': pitch_label,
        'yaw': yaw_label,
        'lat': lat_label,
        'lon': lon_label,
        'alt': alt_label,
        'flight_mode': flight_mode_label,
        'armed': armed_label,
        'imu': imu_label,
        'gps': gps_label,
        'battery': battery_label
    }

    return data_tab, labels_dict, com_port_box, baud_rate_box, update_map


def main():
    """Main entry point for GUI application."""
    app = QApplication(sys.argv)
    app.setStyleSheet(dark_stylesheet)

    window = QMainWindow()
    window.setWindowTitle("QuadGCS")
    window.setGeometry(100, 100, 800, 600)

    # Create tab widget
    tabs = QTabWidget()
    window.setCentralWidget(tabs)

    # Add Data tab
    data_tab, labels_dict, com_port_box, baud_rate_box, update_map = create_data_tab()
    tabs.addTab(data_tab, "Data")

    # Setup live update
    setup_timer(labels_dict, com_port_box, baud_rate_box, update_map)

    # Show GUI
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
