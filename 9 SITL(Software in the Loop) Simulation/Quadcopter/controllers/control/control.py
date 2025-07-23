from controller import Robot

robot = Robot()
timestep = int(robot.getBasicTimeStep())

# Devices
motors = [
    robot.getDevice("m1"),
    robot.getDevice("m2"),
    robot.getDevice("m3"),
    robot.getDevice("m4")
]
inertial_unit = robot.getDevice("inertial unit")
gps = robot.getDevice("gps")

# Enable sensors
inertial_unit.enable(timestep)
gps.enable(timestep)

# Set motor velocities (in rad/s, up to max 100)
velocities = [54,55,54,55]  # Slight differences to test stability
for i in range(4):
    motors[i].setPosition(float('inf'))  # Velocity control mode
    motors[i].setVelocity(velocities[i])

# Main loop
while robot.step(timestep) != -1:
    # Get orientation (roll, pitch, yaw)
    orientation = inertial_unit.getRollPitchYaw()
    roll, pitch, yaw = orientation

    # Get GPS data
    position = gps.getValues()
    speed = gps.getSpeed()

    # Print all sensor data
    print(f"Orientation [rad] => Roll: {roll:.3f}, Pitch: {pitch:.3f}, Yaw: {yaw:.3f}")
    print(f"GPS Position [m]  => x: {position[0]:.3f}, y: {position[1]:.3f}, z: {position[2]:.3f}")
    print(f"Speed [m/s]       => {speed:.3f}")
    print("-" * 60)
