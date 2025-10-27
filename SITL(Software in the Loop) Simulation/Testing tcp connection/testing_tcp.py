import socket
import struct
import threading
import time

HOST = '127.0.0.1'
RECV_PORT = 55000   # Simulink -> Python
SEND_PORT = 55001   # Python -> Simulink

# --- TCP Server to RECEIVE from Simulink ---
def recv_thread():
    recv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    recv_sock.bind((HOST, RECV_PORT))
    recv_sock.listen(1)
    print(f"[RECV] Waiting for Simulink on port {RECV_PORT}...")
    conn, addr = recv_sock.accept()
    print(f"[RECV] Connected to {addr}")
    while True:
        try:
            data = conn.recv(8)
            if not data:
                break
            val = struct.unpack('>d', data)[0]
            print(f"[RECV] Got: {val}")
            # save latest value globally
            global last_value
            last_value = val
        except:
            break
    conn.close()
    recv_sock.close()

# --- TCP Server to SEND to Simulink ---
def send_thread():
    send_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    send_sock.bind((HOST, SEND_PORT))
    send_sock.listen(1)
    print(f"[SEND] Waiting for Simulink on port {SEND_PORT}...")
    conn, addr = send_sock.accept()
    print(f"[SEND] Connected to {addr}")
    while True:
        try:
            val = last_value * 2  # just double the received value
            conn.sendall(struct.pack('>d', val))
            print(f"[SEND] Sent: {val}")
            time.sleep(0.1)
        except:
            break
    conn.close()
    send_sock.close()

last_value = 0.0

# Start both servers
threading.Thread(target=recv_thread, daemon=True).start()
threading.Thread(target=send_thread, daemon=True).start()

# Keep running
while True:
    time.sleep(0.1)
