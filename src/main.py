import socket
import threading
import logging
import command
import myParser
import gui  # Importing the GUI file

# --- Configuration ---
HOST = "127.0.0.1"
PORT = 65525

# Initialize your original classes
p = myParser.Parser()
cur_command = command.Commands()


# --- Class to capture response (replaces print) ---
class DummyConn:
    """This class pretends to be a socket but stores text in a variable."""

    def __init__(self):
        self.response = ""

    def sendall(self, data):
        # If bytes arrive, decode them; otherwise convert to string
        if isinstance(data, bytes):
            self.response += data.decode('utf-8')
        else:
            self.response += str(data)


# --- Mediator (Adapter) for GUI ---
class BankAdapter:
    """
    This class connects your 'cur_command' with 'gui.py'.
    The GUI expects an object with attributes my_ip, my_port, and a method execute_command.
    """

    def __init__(self, ip, port, logic_handler):
        self.my_ip = ip
        self.my_port = port
        self.logic_handler = logic_handler

    def execute_command(self, msg):
        # 1. Create a fake connection to capture the response
        dummy_conn = DummyConn()

        # 2. Run your logic (just like you had in local_command_loop)
        try:
            # We assume logic_handler.execute handles the parsing internally or
            # expects a raw string. If your logic needs parsed list, adapted here.
            # Based on your previous code, execute took 'msg' which came from parser.
            # For local commands from GUI, we pass the raw string string.
            # If your 'execute' needs a list, we might need: parts = msg.split()
            self.logic_handler.execute(msg, dummy_conn)
        except Exception as e:
            return f"ER Execution error: {e}"

        # 3. Return the text that the logic "sent" (sendall)
        return dummy_conn.response


# --- Server part (Logic unchanged, just added logging for GUI) ---
def listen():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Added reuseaddr so the server can be restarted immediately
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((HOST, PORT))
            s.listen()
            logging.info(f"Server listening on {HOST}:{PORT}")  # Shows in GUI
        except Exception as e:
            logging.error(f"Cannot start server: {e}")
            return

        while True:
            try:
                conn, addr = s.accept()
                threading.Thread(target=handle_peer, args=(conn, addr), daemon=True).start()
            except Exception as e:
                logging.error(f"Accept error: {e}")


def handle_peer(conn, addr):
    # Logging to GUI
    logging.info(f"Peer connected: {addr[0]}")
    with conn:
        try:
            data = conn.recv(1024)
            if not data:
                return

            # Your original parsing
            decoded_data = data.decode('utf-8') if isinstance(data, bytes) else data
            msg = p.parse(decoded_data)

            if isinstance(msg, str) and msg.startswith("ER"):
                conn.sendall(msg.encode())
            else:
                cur_command.execute(msg, conn)
                logging.info(f"Command from {addr[0]}: {msg}")  # Info to GUI
        except Exception as e:
            logging.error(f"Communication error with {addr[0]}: {e}")


# --- Main Entry Point ---
if __name__ == "__main__":
    # Setup logging (so it works inside the GUI window)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

    # Start server in background
    server_thread = threading.Thread(target=listen, daemon=True)
    server_thread.start()

    # Create adapter for GUI
    bank_node_adapter = BankAdapter(HOST, PORT, cur_command)

    # Start GUI
    # We pass the adapter which acts like the bank_node object
    app = gui.BankGUI(bank_node_adapter)
    app.start()