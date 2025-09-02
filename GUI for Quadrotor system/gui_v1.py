import sys
import serial
import serial.tools.list_ports
import subprocess
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from dark_theme import dark_stylesheet


def create_tab1():
    main_layout = QVBoxLayout()

    # --- Serial Config (Left) ---
    serial_group = QGroupBox("Serial Port Configuration")
    serial_group.setFixedWidth(200)
    serial_layout = QVBoxLayout()

    port_label = QLabel("Port")
    port_combo = QComboBox()

    baud_label = QLabel("Baud")
    baud_combo = QComboBox()

    status_label = QLabel("❌ Disconnected")
    status_label.setStyleSheet("color: red")
    status_label.setAlignment(Qt.AlignCenter)

    serial_layout.addWidget(port_label)
    serial_layout.addWidget(port_combo)
    serial_layout.addWidget(baud_label)
    serial_layout.addWidget(baud_combo)
    serial_layout.addWidget(QLabel("Status:"))
    serial_layout.addWidget(status_label)
    serial_layout.addStretch()
    serial_group.setFixedHeight(250)
    serial_group.setLayout(serial_layout)

    serial_connection = {"connected": False, "port": None}

    def refresh_ports():
        port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            port_combo.addItem(port.device)

    refresh_ports()
    for rate in ["9600", "19200", "38400", "57600", "115200"]:
        baud_combo.addItem(rate)

    # --- Connect / Refresh buttons under serial group ---
    connect_btn = QPushButton("Connect")
    refresh_btn = QPushButton("Refresh")

    button_row = QHBoxLayout()
    button_row.addWidget(connect_btn)
    button_row.addWidget(refresh_btn)

    serial_container = QVBoxLayout()
    serial_container.addWidget(serial_group)
    serial_container.addLayout(button_row)
    serial_container.addStretch()
    serial_box = QWidget()
    serial_box.setLayout(serial_container)

    # --- Firmware Upload (Right) ---
    upload_group = QGroupBox("Firmware Upload")
    upload_layout = QVBoxLayout()

    upload_fc_btn = QPushButton("Upload FC (DFU)")
    upload_fc_btn.setStyleSheet("background-color: green; color: white;")

    upload_gcs_btn = QPushButton("Upload GCS (COM)")
    upload_gcs_btn.setStyleSheet("background-color: green; color: white;")
    
    upload_status = QLabel("")
    upload_status.setStyleSheet("color: lightblue")

    def handle_upload_fc():
        firmware_file, _ = QFileDialog.getOpenFileName(None, "Select FC Firmware", "", "Binary Files (*.bin)")
        if firmware_file:
            upload_status.setText("Uploading FC firmware...")
            try:
                subprocess.run(["dfu-util", "-a", "0", "-D", firmware_file], check=True)
                upload_status.setText("✅ FC firmware uploaded")
            except Exception:
                upload_status.setText("❌ FC upload failed")

    def handle_upload_gcs():
        firmware_file, _ = QFileDialog.getOpenFileName(None, "Select GCS Firmware", "", "HEX Files (*.hex)")
        port = port_combo.currentText()
        if not port or not firmware_file:
            upload_status.setText("❌ Port or file missing")
            return
        upload_status.setText(f"Uploading GCS firmware to {port}...")
        try:
            subprocess.run([
                "avrdude", "-p", "m328p", "-c", "arduino",
                "-P", port, "-b", "115200",
                "-U", f"flash:w:{firmware_file}:i"
            ], check=True)
            upload_status.setText("✅ GCS firmware uploaded")
        except Exception:
            upload_status.setText("❌ GCS upload failed")

    upload_fc_btn.clicked.connect(handle_upload_fc)
    upload_gcs_btn.clicked.connect(handle_upload_gcs)

    upload_layout.addWidget(upload_fc_btn)
    upload_layout.addWidget(upload_gcs_btn)
    upload_layout.addWidget(upload_status)
    upload_layout.addStretch()
    upload_group.setFixedHeight(130)
    upload_group.setLayout(upload_layout)

    upload_container = QVBoxLayout()
    upload_container.addWidget(upload_group)
    upload_container.addStretch()
    upload_box = QWidget()
    upload_box.setLayout(upload_container)

    # --- Top Row Layout ---
    top_row_layout = QHBoxLayout()
    top_row_layout.addWidget(serial_box, alignment=Qt.AlignTop)
    top_row_layout.addStretch()
    top_row_layout.addWidget(upload_box, alignment=Qt.AlignTop)

    # --- Connect Logic ---
    def handle_connect():
        if not serial_connection["connected"]:
            port = port_combo.currentText()
            baud = baud_combo.currentText()
            if port:
                try:
                    ser = serial.Serial(port, baudrate=int(baud), timeout=1)
                    ser.close()
                    serial_connection["connected"] = True
                    serial_connection["port"] = port
                    connect_btn.setText("Disconnect")
                    status_label.setText("🔌 Connected")
                    status_label.setStyleSheet("color: lightgreen")
                except Exception:
                    status_label.setText("❌ Error")
                    status_label.setStyleSheet("color: orange")
        else:
            serial_connection["connected"] = False
            serial_connection["port"] = None
            connect_btn.setText("Connect")
            status_label.setText("❌ Disconnected")
            status_label.setStyleSheet("color: red")

    connect_btn.clicked.connect(handle_connect)
    refresh_btn.clicked.connect(refresh_ports)

    # --- Final Assembly ---
    main_layout.addLayout(top_row_layout)
    main_layout.addSpacing(10)
    main_layout.addStretch()

    widget = QWidget()
    widget.setLayout(main_layout)
    return widget

def create_tab2():
    layout = QVBoxLayout()
    layout.addWidget(QLabel("📊 Data Monitoring and Visualization"))
    widget = QWidget()
    widget.setLayout(layout)
    return widget


def create_tab3():
    layout = QVBoxLayout()
    layout.addWidget(QLabel("🧪 System Diagnostics"))
    widget = QWidget()
    widget.setLayout(layout)
    return widget


def setup_ui():
    app = QApplication(sys.argv)
    app.setStyleSheet(dark_stylesheet)

    window = QWidget()
    window.setWindowTitle("Quadcopter GUI")

    tabs = QTabWidget()
    tabs.setTabPosition(QTabWidget.North)
    tabs.setMovable(False)

    tabs.addTab(create_tab1(), "🛠️ Configuration and Setup")
    tabs.addTab(create_tab2(), "📊 Data Monitoring and Visualization")
    tabs.addTab(create_tab3(), "🧪 System Diagnostics")

    main_layout = QVBoxLayout()
    main_layout.addWidget(tabs)
    window.setLayout(main_layout)

    window.resize(900, 600)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    setup_ui()
