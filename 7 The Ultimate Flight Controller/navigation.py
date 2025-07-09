import math

def navigation(mpu6050_list, gps_list, mag_list, baro_list):
    """
    Inputs:
        mpu6050_list: [[ax, ay, az, gx, gy, gz], ...]
        gps_list    : [[lat, lon, alt], ...]
        mag_list    : [[mx, my, mz], ...]
        baro_list   : [[pressure, temp, humidity], ...]

    Output:
        [lat, lon, alt, roll_deg, pitch_deg, yaw_deg]
    """

    # -------------------------------
    # 1. Initialize persistent state
    # -------------------------------
    if not hasattr(navigation, "prev_state"):
        navigation.prev_state = [0.0, 0.0, 0.0, 0.0]  # roll, pitch, yaw, alt

    prev_roll, prev_pitch, prev_yaw, prev_alt = navigation.prev_state

    # -------------------------------
    # 2. Constants
    # -------------------------------
    P0 = 101325
    ACCEL_SCALE = 9.80665 / 16384.0
    GYRO_SCALE = (math.pi / 180) / 131.0

    ALPHA_RPY = 0.98
    ALPHA_ALT = 0.95

    ORIENTATION_ANGLES = {
        'mpu6050': 15,
        'mag': 10,
        'baro': 0,
        'gps': 0
    }

    # -------------------------------
    # 3. Helpers
    # -------------------------------
    def rotate_z(vec, angle_deg):
        angle_rad = math.radians(angle_deg)
        x, y, z = vec
        x_new = x * math.cos(angle_rad) - y * math.sin(angle_rad)
        y_new = x * math.sin(angle_rad) + y * math.cos(angle_rad)
        return [x_new, y_new, z]

    def average(vectors):
        n = len(vectors)
        return [sum(v[i] for v in vectors) / n for i in range(len(vectors[0]))]

    # -------------------------------
    # 4. Convert and rotate each sensor
    # -------------------------------
    acc_list = []
    gyro_list = []

    for v in mpu6050_list:
        acc_raw = [v[i] * ACCEL_SCALE for i in range(3)]
        gyro_raw = [v[i] * GYRO_SCALE for i in range(3, 6)]
        acc_rot = rotate_z(acc_raw, ORIENTATION_ANGLES['mpu6050'])
        gyro_rot = rotate_z(gyro_raw, ORIENTATION_ANGLES['mpu6050'])
        acc_list.append(acc_rot)
        gyro_list.append(gyro_rot)

    mag_rot_list = [rotate_z(m, ORIENTATION_ANGLES['mag']) for m in mag_list]

    acc_avg = average(acc_list)
    gyro_avg = average(gyro_list)
    mag_avg = average(mag_rot_list)
    gps_avg = average(gps_list)
    baro_avg = average(baro_list)

    # -------------------------------
    # 5. Compute angles and altitude
    # -------------------------------
    acc_roll  = math.atan2(acc_avg[1], acc_avg[2])
    acc_pitch = math.atan2(-acc_avg[0], math.sqrt(acc_avg[1]**2 + acc_avg[2]**2))

    mag_x = mag_avg[0] * math.cos(acc_pitch) + mag_avg[2] * math.sin(acc_pitch)
    mag_y = (mag_avg[0] * math.sin(acc_roll) * math.sin(acc_pitch) +
             mag_avg[1] * math.cos(acc_roll) -
             mag_avg[2] * math.sin(acc_roll) * math.cos(acc_pitch))
    mag_yaw = math.atan2(-mag_y, mag_x)

    pressure = baro_avg[0]
    gps_alt = gps_avg[2]
    alt_baro = 44330 * (1 - (pressure / P0) ** 0.1903)

    # -------------------------------
    # 6. Complementary filter
    # -------------------------------
    roll  = ALPHA_RPY * (prev_roll  + gyro_avg[0]) + (1 - ALPHA_RPY) * acc_roll
    pitch = ALPHA_RPY * (prev_pitch + gyro_avg[1]) + (1 - ALPHA_RPY) * acc_pitch
    yaw   = ALPHA_RPY * (prev_yaw   + gyro_avg[2]) + (1 - ALPHA_RPY) * mag_yaw
    alt   = ALPHA_ALT * alt_baro + (1 - ALPHA_ALT) * gps_alt

    # -------------------------------
    # 7. Save updated state
    # -------------------------------
    navigation.prev_state = [roll, pitch, yaw, alt]

    # -------------------------------
    # 8. Return
    # -------------------------------
    return [
        gps_avg[0],  # lat
        gps_avg[1],  # lon
        alt,
        math.degrees(roll),
        math.degrees(pitch),
        math.degrees(yaw)
    ]


mpu = [[200, 1000, 16000, 10, -15, 3], [210, 990, 15990, 9, -14, 2]]
gps = [[12.9716, 77.5946, 890.0], [12.9717, 77.5945, 891.0]]
mag = [[30.0, 5.0, -40.0], [29.0, 6.0, -41.0]]
baro = [[100800, 25.0, 45.0], [100790, 25.5, 46.0]]

print(navigation(mpu, gps, mag, baro))  # First call
print(navigation(mpu, gps, mag, baro))  # Second call, uses updated prev_state
