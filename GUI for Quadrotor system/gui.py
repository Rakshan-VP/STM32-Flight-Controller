import sys
import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTabWidget, QMainWindow, QComboBox, QPushButton, QGridLayout
)
from PyQt5.QtGui import QIcon
from dark_theme import dark_stylesheet
from data import (
    setup_timer, create_map_widget, create_rpy_plot, create_motor_pwm_plot
)


def create_data_tab():
    data_tab = QWidget()
    main_layout = QVBoxLayout()

    # -----------------------
    # Top bar
    # -----------------------
    top_bar = QHBoxLayout()
    top_bar.addStretch()

    com_port_box = QComboBox()
    ports = serial.tools.list_ports.comports()
    for port in ports:
        com_port_box.addItem(port.device)
    top_bar.addWidget(com_port_box)

    baud_rate_box = QComboBox()
    baud_rate_box.addItems(["9600", "57600", "115200"])
    top_bar.addWidget(baud_rate_box)

    connect_button = QPushButton("CONNECT")
    top_bar.addWidget(connect_button)
    main_layout.addLayout(top_bar)

    # -----------------------
    # Middle bar
    # -----------------------
    middle_bar = QHBoxLayout()

    # Left layout for labels
    left_layout = QVBoxLayout()
    grid_layout = QGridLayout()

    roll_label = QLabel("0.0")
    pitch_label = QLabel("0.0")
    yaw_label = QLabel("0.0")
    grid_layout.addWidget(QLabel("Roll:"), 0, 0)
    grid_layout.addWidget(roll_label, 0, 1)
    grid_layout.addWidget(QLabel("Pitch:"), 1, 0)
    grid_layout.addWidget(pitch_label, 1, 1)
    grid_layout.addWidget(QLabel("Yaw:"), 2, 0)
    grid_layout.addWidget(yaw_label, 2, 1)

    lat_label = QLabel("0.0")
    lon_label = QLabel("0.0")
    alt_label = QLabel("0.0")
    grid_layout.addWidget(QLabel("Latitude:"), 0, 2)
    grid_layout.addWidget(lat_label, 0, 3)
    grid_layout.addWidget(QLabel("Longitude:"), 1, 2)
    grid_layout.addWidget(lon_label, 1, 3)
    grid_layout.addWidget(QLabel("Altitude:"), 2, 2)
    grid_layout.addWidget(alt_label, 2, 3)

    left_layout.addLayout(grid_layout)

    flight_mode_label = QLabel("Flight Mode: ---")
    armed_label = QLabel("Armed: ---")
    imu_label = QLabel("IMU: ---")
    gps_label = QLabel("GPS: ---")
    battery_label = QLabel("Battery: ---")
    left_layout.addWidget(flight_mode_label)
    left_layout.addWidget(armed_label)
    left_layout.addWidget(imu_label)
    left_layout.addWidget(gps_label)
    left_layout.addWidget(battery_label)
    left_layout.addStretch()

    middle_bar.addLayout(left_layout)

    # Right layout for map
    right_layout = QVBoxLayout()
    map_widget, update_map = create_map_widget()
    right_layout.addWidget(map_widget)
    middle_bar.addLayout(right_layout)

    main_layout.addLayout(middle_bar)

    # -----------------------
    # Bottom bar with plots
    # -----------------------
    rpy_rate_widget, update_rpy_rates = create_rpy_plot()
    motor_pwm_widget, update_motor_pwms = create_motor_pwm_plot()
    main_layout.addWidget(rpy_rate_widget)
    main_layout.addWidget(motor_pwm_widget)

    data_tab.setLayout(main_layout)

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

    return data_tab, labels_dict, com_port_box, baud_rate_box, update_map, update_rpy_rates, update_motor_pwms


def def_config_tab():
    """Create Config & Settings tab layout"""
    tab = QWidget()
    layout = QVBoxLayout(tab)
    layout.addStretch()  # Placeholder, can add widgets later
    return tab


def def_logs_tab():
    """Create Logs & Firmware tab layout"""
    tab = QWidget()
    layout = QVBoxLayout(tab)
    layout.addStretch()
    return tab


def def_testing_tab():
    """Create Testing tab layout"""
    tab = QWidget()
    layout = QVBoxLayout(tab)
    layout.addStretch()
    return tab


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(dark_stylesheet)

    window = QMainWindow()
    window.setWindowIcon(QIcon("GUI for Quadrotor system\logo.ico"))
    window.setWindowTitle("QuadGCS")
    window.setGeometry(100, 100, 1200, 850)
    
    tabs = QTabWidget()
    window.setCentralWidget(tabs)

    # Data tab
    data_tab, labels_dict, com_port_box, baud_rate_box, update_map, update_rpy_rates, update_motor_pwms = create_data_tab()
    tabs.addTab(data_tab, "Data")
    tabs.addTab(def_config_tab(), "Config and Settings")
    tabs.addTab(def_logs_tab(), "Logs and Firmware")
    tabs.addTab(def_testing_tab(), "Testing")

    # Setup timer
    setup_timer(
        labels_dict,
        com_port_box,
        baud_rate_box,
        update_map,
        update_rpy_rates,
        update_motor_pwms
    )

    window.show()
    sys.exit(app.exec_())



if __name__ == "__main__":
    main()
