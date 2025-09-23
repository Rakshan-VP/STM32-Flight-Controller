# functions.py
import serial
from PyQt5.QtCore import QTimer

def read_com_data(port_name, baud_rate):
    """
    Read a line of data from the COM port and return parsed values.
    Expected format: roll,pitch,yaw,lat,lon,alt
    """
    try:
        ser = serial.Serial(port_name, baud_rate, timeout=0.1)
        line = ser.readline().decode("utf-8").strip()
        if line:
            parts = line.split(",")
            if len(parts) >= 6:
                roll = float(parts[0])
                pitch = float(parts[1])
                yaw = float(parts[2])
                lat = float(parts[3])
                lon = float(parts[4])
                alt = float(parts[5])
                return roll, pitch, yaw, lat, lon, alt
    except Exception as e:
        print("COM read error:", e)
    return None, None, None, None, None, None

def setup_timer(labels_dict, com_port_box, baud_rate_box, app):
    """
    Setup a QTimer to update the labels periodically.
    labels_dict: {'roll': QLabel, 'pitch': QLabel, ...}
    """
    def update_labels():
        roll, pitch, yaw, lat, lon, alt = read_com_data(
            com_port_box.currentText(),
            int(baud_rate_box.currentText())
        )
        if roll is not None:
            labels_dict['roll'].setText(f"{roll:.2f}")
            labels_dict['pitch'].setText(f"{pitch:.2f}")
            labels_dict['yaw'].setText(f"{yaw:.2f}")
            labels_dict['lat'].setText(f"{lat:.6f}")
            labels_dict['lon'].setText(f"{lon:.6f}")
            labels_dict['alt'].setText(f"{alt:.2f}")

    timer = QTimer()
    timer.timeout.connect(update_labels)
    timer.start(100)  # update every 100 ms
