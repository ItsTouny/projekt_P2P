import socket
import multiprocessing
import logging
from command import Commands
import gui
import loadConfig

config = loadConfig.load_config()

HOST = config["IP"]
PORT = config["PORT"]
TIMEOUT = config["timeout"]

class DummyConn:
    def __init__(self):
        self.response = ""

    def sendall(self, data):
        if isinstance(data, bytes):
            self.response += data.decode('utf-8')
        else:
            self.response += str(data)

class BankAdapter:
    def __init__(self, ip, port, lock):
        self.my_ip = ip
        self.my_port = port
        self.lock = lock
        self.commands = Commands(lock)

    def execute_command(self, msg):
        dummy_conn = DummyConn()
        try:
            self.commands.execute(msg, dummy_conn)
        except Exception as e:
            return f"ER Chyba: {e}"
        return dummy_conn.response

def handle_client(conn, addr, lock):
    logging.info(f"Nové spojení: {addr}")
    commands = Commands(lock)
    conn.setblocking(True)

    with conn:
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                message = data.decode().strip()
                logging.info(f"Command from {addr}: {message}")
                commands.execute(message, conn)
            except Exception as e:
                logging.error(f"Communication error: {e}")
                break


def setup_server_socket():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    s.setblocking(False)
    logging.info(f"Server running on {HOST}:{PORT}")
    return s


def check_for_clients(server_socket, lock, app_root):
    try:
        conn, addr = server_socket.accept()

        p = multiprocessing.Process(
            target=handle_client,
            args=(conn, addr, lock)
        )
        p.daemon = True
        p.start()

    except BlockingIOError:
        pass
    except Exception as e:
        logging.error(f"Socket error: {e}")

    app_root.after(100, check_for_clients, server_socket, lock, app_root)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

    lock = multiprocessing.Lock()

    server_socket = setup_server_socket()

    adapter = BankAdapter(HOST, PORT, lock)
    app = gui.BankGUI(adapter)

    check_for_clients(server_socket, lock, app.root)

    app.start()