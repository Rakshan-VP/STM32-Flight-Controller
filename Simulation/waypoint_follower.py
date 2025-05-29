import math
import matplotlib.pyplot as plt

# Parameters

TRANSITION_RADIUS = 0.4  # Start transitioning early
MAX_SPEED = 1.0
DT = 0.1
KP = 5.0
KD = 0.5
ALPHA = 0.2  # Low-pass filter strength

launch_point = (0, 0, 0)
waypoints = [
    (5, 0, 5),
    (5, 5, 10),
    (0, 5, 7)
]

def distance(p1, p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 + (p1[2]-p2[2])**2)

def velocity_command(current_pos, waypoint, prev_error, dt):
    error = tuple(wp - cp for wp, cp in zip(waypoint, current_pos))
    d_error = tuple((e - pe)/dt for e, pe in zip(error, prev_error))
    vx, vy, vz = [KP*e + KD*de for e, de in zip(error, d_error)]

    speed = math.sqrt(vx**2 + vy**2 + vz**2)
    if speed > MAX_SPEED:
        scale = MAX_SPEED / speed
        vx *= scale
        vy *= scale
        vz *= scale

    return (vx, vy, vz), error

def update_position(pos, vel, dt):
    return tuple(p + v*dt for p, v in zip(pos, vel))

def velocity_to_rpy(vx, vy, vz):
    yaw = math.atan2(vy, vx)
    horizontal_speed = math.sqrt(vx*vx + vy*vy)
    pitch = math.atan2(vz, horizontal_speed)
    roll = 0.0
    return math.degrees(roll), math.degrees(pitch), math.degrees(yaw)

def low_pass_filter(current, previous, alpha):
    return tuple(alpha * c + (1 - alpha) * p for c, p in zip(current, previous))

def run_waypoint_follower(waypoints, launch_point, rtl_enabled):
    current_pos = launch_point
    current_wp_index = 0
    time = 0.0
    traj = []
    prev_error = (0.0, 0.0, 0.0)
    prev_velocity = (0.0, 0.0, 0.0)
    prev_rpy = (0.0, 0.0, 0.0)

    mission_wps = waypoints.copy()
    if rtl_enabled:
        mission_wps.append(launch_point)
    else:
        last = waypoints[-1]
        mission_wps.append((last[0], last[1], 0))

    while current_wp_index < len(mission_wps):
        target_wp = mission_wps[current_wp_index]
        (vx, vy, vz), prev_error = velocity_command(current_pos, target_wp, prev_error, DT)
        
        # Apply smoothing
        vx, vy, vz = low_pass_filter((vx, vy, vz), prev_velocity, ALPHA)
        prev_velocity = (vx, vy, vz)

        current_pos = update_position(current_pos, (vx, vy, vz), DT)
        roll, pitch, yaw = velocity_to_rpy(vx, vy, vz)
        roll, pitch, yaw = low_pass_filter((roll, pitch, yaw), prev_rpy, ALPHA)
        prev_rpy = (roll, pitch, yaw)

        traj.append((time, roll, pitch, yaw, current_pos))

        # Smooth transition
        if distance(current_pos, target_wp) < TRANSITION_RADIUS:
            print(f"Transitioning from WP {current_wp_index}")
            current_wp_index += 1
            prev_error = (0.0, 0.0, 0.0)
            continue

        time += DT
        if time > 300:
            print("Timeout.")
            break

    return traj

# --- Run and Plot ---
if __name__ == "__main__":
    traj = run_waypoint_follower(waypoints, launch_point, rtl_enabled=False)

    ts = [t for t, _, _, _, _ in traj]
    xs = [p[0] for _, _, _, _, p in traj]
    ys = [p[1] for _, _, _, _, p in traj]
    zs = [p[2] for _, _, _, _, p in traj]
    rolls = [r for _, r, _, _, _ in traj]
    pitches = [p for _, _, p, _, _ in traj]
    yaws = [y for _, _, _, y, _ in traj]

    plt.figure(figsize=(12, 9))

    # Subplot 1: XY path
    plt.subplot(3, 1, 1)
    plt.plot(xs, ys, label='XY Path')
    plt.scatter(*zip(*[(w[0], w[1]) for w in waypoints]), c='red', marker='x', label='Waypoints')
    plt.scatter(launch_point[0], launch_point[1], color='green', marker='o', label='Start')
    for i, wp in enumerate(waypoints):
        plt.text(wp[0], wp[1], f"WP {i+1}")
    plt.xlabel("X (m)")
    plt.ylabel("Y (m)")
    plt.grid()
    plt.legend()
    plt.title("XY Path")

    # Subplot 2: RPY in degrees
    plt.subplot(3, 1, 2)
    plt.plot(ts, rolls, label='Roll (°)')
    plt.plot(ts, pitches, label='Pitch (°)')
    plt.plot(ts, yaws, label='Yaw (°)')
    plt.xlabel("Time (s)")
    plt.ylabel("Angle (°)")
    plt.legend()
    plt.grid()
    plt.title("Orientation")

    # Subplot 3: Altitude
    plt.subplot(3, 1, 3)
    plt.plot(ts, zs, label="Altitude (Z)", color="purple")
    plt.xlabel("Time (s)")
    plt.ylabel("Altitude (m)")
    plt.grid()
    plt.title("Altitude over Time")
    plt.tight_layout()
    plt.legend()

    plt.show()
