import socket
import struct
import threading
import time

HOST = '127.0.0.1'
SEND_PORT = 55000   # Python -> Simulink (commands)
RECV_PORT = 55001   # Simulink -> Python (telemetry)

telemetry = [0.0] * 13
telemetry_time = 0.0
running = True

command_lock = threading.Lock()
current_altitude = 0.0          # current commanded altitude
altitude_expire_time = 0.0      # when to return to [1, 0]
hold_duration = 10.0            # seconds to hold altitude


# -------------------------------------------------------
# RECEIVE telemetry from Simulink
# -------------------------------------------------------
def receive_telemetry():
    global telemetry, telemetry_time, running
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    server.bind((HOST, RECV_PORT))
    server.listen(1)
    print(f"[RECV] Waiting for Simulink on port {RECV_PORT}...")

    conn, addr = server.accept()
    conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    print(f"[RECV] Connected to Simulink at {addr}")

    try:
        while running:
            data = conn.recv(8 * 13)
            if len(data) < 104:
                continue
            telemetry = struct.unpack('>13d', data)
            telemetry_time = telemetry[0]
            print(f"[RECV] Time={telemetry_time:6.2f}s | Telemetry={telemetry}")
    except (ConnectionResetError, BrokenPipeError):
        print("[RECV] Simulink connection closed.")
    finally:
        conn.close()
        server.close()
        print("[RECV] Socket closed.")


# -------------------------------------------------------
# SEND altitude commands (live override + 10s hold)
# -------------------------------------------------------
def send_commands():
    global running, current_altitude, altitude_expire_time
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    server.bind((HOST, SEND_PORT))
    server.listen(1)
    print(f"[SEND] Waiting for Simulink on port {SEND_PORT}...")

    conn, addr = server.accept()
    conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    print(f"[SEND] Connected to Simulink at {addr}")

    next_time = time.perf_counter()
    try:
        while running:
            with command_lock:
                now = time.time()
                # Send [1, current_altitude] while within hold window
                if now <= altitude_expire_time:
                    alt = current_altitude
                else:
                    alt = 0.0  # revert to idle

            # pack + send
            cmd = [1.0, alt]
            conn.sendall(struct.pack('>2d', *cmd))
            print(f"[SEND] Sent: [1, {alt:.2f}]")

            # Maintain 10 Hz update
            next_time += 0.1
            delay = next_time - time.perf_counter()
            if delay > 0:
                time.sleep(delay)
            else:
                next_time = time.perf_counter()
    except (ConnectionResetError, BrokenPipeError):
        print("[SEND] Simulink connection closed.")
    finally:
        conn.close()
        server.close()
        print("[SEND] Socket closed.")


# -------------------------------------------------------
# USER INPUT (can override anytime)
# -------------------------------------------------------
def user_input():
    global current_altitude, altitude_expire_time, running
    try:
        while running:
            user_text = input("\nEnter altitude (m) or 'q' to quit: ").strip()
            if user_text.lower() == 'q':
                running = False
                break
            try:
                alt = float(user_text)
                with command_lock:
                    current_altitude = alt
                    altitude_expire_time = time.time() + hold_duration  # restart timer
                print(f"[INPUT] Altitude {alt:.2f} m → holding for {hold_duration:.0f} s (resets if changed)")
            except ValueError:
                print("⚠️ Please enter a valid number or 'q' to quit.")
    except KeyboardInterrupt:
        running = False


# -------------------------------------------------------
# MAIN
# -------------------------------------------------------
if __name__ == "__main__":
    threading.Thread(target=receive_telemetry, daemon=True).start()
    threading.Thread(target=send_commands, daemon=True).start()
    user_input()

    running = False
    print("Exiting program...")
    time.sleep(0.5)
