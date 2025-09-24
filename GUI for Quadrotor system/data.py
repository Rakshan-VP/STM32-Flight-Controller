# data.py
import serial
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


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


def create_map_widget():
    """
    Create a matplotlib map widget for showing Lat/Lon position.
    Returns the QWidget and update_map function.
    """
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # Setup matplotlib figure
    fig = Figure(figsize=(5, 4))
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)
    ax.set_title("Drone Path")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(True)

    # Store path
    lat_data, lon_data = [], []
    line, = ax.plot([], [], 'ro-', markersize=4)  # red path

    layout.addWidget(canvas)

    def update_map(lat, lon):
        if lat is not None and lon is not None:
            lat_data.append(lat)
            lon_data.append(lon)
            line.set_data(lon_data, lat_data)
            ax.relim()
            ax.autoscale_view()
            canvas.draw_idle()

    return widget, update_map


def setup_timer(labels_dict, com_port_box, baud_rate_box, update_map_func):
    """
    Setup a QTimer to update the labels and map periodically.

    labels_dict: {
        'roll': QLabel, 'pitch': QLabel, 'yaw': QLabel,
        'lat': QLabel, 'lon': QLabel, 'alt': QLabel,
        'flight_mode': QLabel, 'armed': QLabel,
        'imu': QLabel, 'gps': QLabel, 'battery': QLabel
    }

    update_map_func: function(lat, lon) from create_map_widget()
    """
    def update_labels():
        # Read data from COM port
        try:
            port_name = com_port_box.currentText()
            baud_rate = int(baud_rate_box.currentText())
            ser = serial.Serial(port_name, baud_rate, timeout=0.1)
            line = ser.readline().decode("utf-8").strip()
            ser.close()
        except Exception as e:
            print("COM read error:", e)
            line = ""

        if line:
            parts = line.split(",")
            # Roll, Pitch, Yaw, Lat, Lon, Alt
            if len(parts) >= 6:
                roll = float(parts[0])
                pitch = float(parts[1])
                yaw = float(parts[2])
                lat = float(parts[3])
                lon = float(parts[4])
                alt = float(parts[5])

                labels_dict['roll'].setText(f"{roll:.2f}")
                labels_dict['pitch'].setText(f"{pitch:.2f}")
                labels_dict['yaw'].setText(f"{yaw:.2f}")
                labels_dict['lat'].setText(f"{lat:.6f}")
                labels_dict['lon'].setText(f"{lon:.6f}")
                labels_dict['alt'].setText(f"{alt:.2f}")
                update_map_func(lat, lon)

            # Flight Mode, Armed, IMU, GPS, Battery
            if len(parts) >= 11:
                labels_dict['flight_mode'].setText(f"Flight Mode: {parts[6]}")
                labels_dict['armed'].setText(f"Armed: {parts[7]}")
                labels_dict['imu'].setText(f"IMU: {parts[8]}")
                labels_dict['gps'].setText(f"GPS: {parts[9]}")
                labels_dict['battery'].setText(f"Battery: {parts[10]}")

    timer = QTimer()
    timer.timeout.connect(update_labels)
    timer.start(100)  # update every 100 ms

