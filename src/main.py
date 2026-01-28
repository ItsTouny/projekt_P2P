import socket
import multiprocessing
import subprocess
import sys
import time
import os
from command import Commands
from config_loader import load_config

CONFIG = load_config()
PORT = CONFIG["port"]
CLIENT_TIMEOUT = CONFIG["client_timeout"]


def handle_client(conn, addr, lock):
    """
    Handles a single client connection.
    If the connection times out due to inactivity, sends a notification message
    to the client before closing the connection.

    Args:
        conn (socket.socket): Client connection socket.
        addr (tuple): Client address info (IP, Port).
        lock (multiprocessing.RLock): Shared re-entrant lock.
    """
    commands = Commands(lock)
    client_ip = addr[0]

    conn.settimeout(CLIENT_TIMEOUT)

    with conn:
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                commands.execute(data.decode().strip(), conn, addr=client_ip)
            except socket.timeout:
                try:
                    msg = "TIMEOUT: Connection closed due to inactivity.\r\n"
                    conn.sendall(msg.encode())
                except OSError:
                    pass
                break
            except ConnectionResetError:
                break


def run_server_process():
    """
    Initializes and runs the TCP server.
    Spawns a new process for each incoming connection.
    """
    lock = multiprocessing.RLock()
    commands = Commands(lock)
    host = commands.get_my_ip()

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, PORT))
            s.listen()

            while True:
                conn, addr = s.accept()
                p = multiprocessing.Process(
                    target=handle_client,
                    args=(conn, addr, lock),
                    daemon=True
                )
                p.start()
    except OSError:
        pass


if __name__ == "__main__":
    multiprocessing.freeze_support()

    server_process = multiprocessing.Process(target=run_server_process, daemon=False)
    server_process.start()

    time.sleep(1)

    ui_path = "src/ui.py" if os.path.exists("src/ui.py") else "ui.py"

    try:
        ui = subprocess.Popen([sys.executable, ui_path])
        ui.wait()
    except KeyboardInterrupt:
        pass
    finally:
        server_process.terminate()
        server_process.join()