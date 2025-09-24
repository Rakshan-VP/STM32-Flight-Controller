import serial
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# -------------------------------
# COM data reading
# -------------------------------
def read_com_data(port_name, baud_rate):
    """
    Read a line of data from the COM port and return parsed values.
    Expected format: roll,pitch,yaw,lat,lon,alt,m1,m2,m3,m4,flight_mode,armed,imu,gps,battery
    """
    try:
        ser = serial.Serial(port_name, baud_rate, timeout=0.1)
        line = ser.readline().decode("utf-8").strip()
        ser.close()
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


# -------------------------------
# Map widget
# -------------------------------
def create_map_widget():
    widget = QWidget()
    layout = QVBoxLayout(widget)

    fig = Figure(figsize=(5, 3), facecolor='black')
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111, facecolor='black')

    ax.set_title("Drone Path", color='white')
    ax.set_xlabel("Longitude", color='white')
    ax.set_ylabel("Latitude", color='white')
    ax.tick_params(colors='white')
    ax.grid(True, color='gray', linestyle='--', alpha=0.5)

    lat_data, lon_data = [], []
    line, = ax.plot([], [], 'ro-', markersize=4)

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


# -------------------------------
# RPY plot
# -------------------------------
def create_rpy_plot():
    widget = QWidget()
    layout = QVBoxLayout(widget)

    fig = Figure(figsize=(5, 2), facecolor='black')
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111, facecolor='black')

    ax.set_title("Roll / Pitch / Yaw Rate", color='white')
    ax.set_xlabel("Time (s)", color='white')
    ax.set_ylabel("Degrees / deg/s", color='white')
    ax.tick_params(colors='white')
    ax.grid(True, color='gray', linestyle='--', alpha=0.5)

    time_data, roll_data, pitch_data, yaw_rate_data = [], [], [], []
    roll_line, = ax.plot([], [], 'r-', label='Roll (deg)')
    pitch_line, = ax.plot([], [], 'g-', label='Pitch (deg)')
    yaw_line, = ax.plot([], [], 'b-', label='Yaw Rate (deg/s)')
    ax.legend(facecolor='black', edgecolor='white', labelcolor='white')

    layout.addWidget(canvas)

    def update_rpy_plot(t, roll, pitch, yaw_rate):
        time_data.append(t)
        roll_data.append(roll)
        pitch_data.append(pitch)
        yaw_rate_data.append(yaw_rate)

        roll_line.set_data(time_data, roll_data)
        pitch_line.set_data(time_data, pitch_data)
        yaw_line.set_data(time_data, yaw_rate_data)

        # Sliding window: last 20 seconds
        ax.set_xlim(max(0, t - 20), max(20, t))
        ax.relim()
        ax.autoscale_view(scalex=False, scaley=True)
        canvas.draw_idle()

    return widget, update_rpy_plot


# -------------------------------
# Motor PWM plot
# -------------------------------
def create_motor_pwm_plot():
    widget = QWidget()
    layout = QVBoxLayout(widget)

    fig = Figure(figsize=(5, 2), facecolor='black')
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111, facecolor='black')

    ax.set_title("Motor PWM", color='white')
    ax.set_xlabel("Time (s)", color='white')
    ax.set_ylabel("PWM", color='white')
    ax.set_ylim(900, 2100)
    ax.tick_params(colors='white')
    ax.grid(True, color='gray', linestyle='--', alpha=0.5)

    time_data, m1_data, m2_data, m3_data, m4_data = [], [], [], [], []
    m1_line, = ax.plot([], [], 'r-', label='M1')
    m2_line, = ax.plot([], [], 'g-', label='M2')
    m3_line, = ax.plot([], [], 'b-', label='M3')
    m4_line, = ax.plot([], [], 'y-', label='M4')
    ax.legend(facecolor='black', edgecolor='white', labelcolor='white')

    layout.addWidget(canvas)

    def update_motor_pwms(t, m1, m2, m3, m4):
        time_data.append(t)
        m1_data.append(m1)
        m2_data.append(m2)
        m3_data.append(m3)
        m4_data.append(m4)

        m1_line.set_data(time_data, m1_data)
        m2_line.set_data(time_data, m2_data)
        m3_line.set_data(time_data, m3_data)
        m4_line.set_data(time_data, m4_data)

        ax.set_xlim(max(0, t - 20), max(20, t))
        ax.relim()
        ax.autoscale_view(scalex=False, scaley=True)
        canvas.draw_idle()

    return widget, update_motor_pwms


# -------------------------------
# Timer update
# -------------------------------
def setup_timer(labels_dict, com_port_box, baud_rate_box, update_map_func,
                update_rpy_plot_func=None, update_motor_pwms_func=None):
    prev_yaw = 0
    time_counter = 0

    def update_labels():
        nonlocal prev_yaw, time_counter
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

                if update_rpy_plot_func:
                    dt = 0.1
                    yaw_rate = (yaw - prev_yaw) / dt
                    time_counter += dt
                    update_rpy_plot_func(time_counter, roll, pitch, yaw_rate)
                    prev_yaw = yaw

            if len(parts) >= 11:
                labels_dict['flight_mode'].setText(f"Flight Mode: {parts[6]}")
                labels_dict['armed'].setText(f"Armed: {parts[7]}")
                labels_dict['imu'].setText(f"IMU: {parts[8]}")
                labels_dict['gps'].setText(f"GPS: {parts[9]}")
                labels_dict['battery'].setText(f"Battery: {parts[10]}")

            if len(parts) >= 15 and update_motor_pwms_func:
                m1 = float(parts[11])
                m2 = float(parts[12])
                m3 = float(parts[13])
                m4 = float(parts[14])
                update_motor_pwms_func(time_counter, m1, m2, m3, m4)

    timer = QTimer()
    timer.timeout.connect(update_labels)
    timer.start(100)
