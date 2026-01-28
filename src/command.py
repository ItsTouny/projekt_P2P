import random
import socket
import json
import os
import datetime
from config_loader import load_config

FILE = "accounts.json"
CONFIG = load_config()
P2P_TIMEOUT = CONFIG["p2p_timeout"]
BASE_PORT = CONFIG["port"]


def load_accounts():
    """
    Loads the account database from the JSON file.

    Returns:
        dict: Dictionary of accounts {key: balance}.
    """
    if not os.path.exists(FILE):
        return {}
    with open(FILE, "r") as f:
        return json.load(f)


def save_accounts(accounts):
    """
    Saves the current state of accounts to the JSON file.

    Args:
        accounts (dict): Dictionary of accounts to save.
    """
    with open(FILE, "w") as f:
        json.dump(accounts, f)


class Commands:
    """
    Class encapsulating banking operation logic, P2P communication, and logging.
    """

    def __init__(self, lock):
        """
        Initializes the commands instance and sets up the logging directory.
        The log file is located in a 'log' directory sibling to the 'src' directory.

        Args:
            lock (multiprocessing.RLock): Lock for safe file access.
        """
        self.lock = lock
        self.commands = {
            "BC": self.bank_code,
            "AC": self.account_create,
            "AD": self.account_deposit,
            "AW": self.account_withdraw,
            "AB": self.account_balance,
            "AR": self.account_remove,
            "BA": self.bank_total,
            "BN": self.bank_number,
        }

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.log_dir = os.path.join(base_dir, "log")
        self.log_file = os.path.join(self.log_dir, "bank.log")

        if not os.path.exists(self.log_dir):
            try:
                os.makedirs(self.log_dir)
            except OSError:
                pass

    def log_event(self, addr, direction, message):
        """
        Appends a log entry to the log file.

        Args:
            addr (str): The address associated with the event.
            direction (str): "IN" for requests, "OUT" for responses.
            message (str): The content of the message.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {addr} [{direction}]: {message}\n"

        with self.lock:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)

    def send_response(self, conn, msg, addr):
        """
        Logs the outgoing response and sends it to the client.

        Args:
            conn (socket.socket): Connection to the client.
            msg (str): Message to send.
            addr (str): Recipient address for logging.
        """
        self.log_event(addr, "OUT", msg)
        conn.sendall((msg + "\r\n").encode())

    def execute(self, message, conn, addr="UNKNOWN"):
        """
        Parses and executes an incoming command, logging both request and response.

        Args:
            message (str): Received text command.
            conn (socket.socket): Client connection or mock connection object.
            addr (str, optional): Source identifier for logging. Defaults to "UNKNOWN".
        """
        if not message:
            return

        self.log_event(addr, "IN", message)

        parts = message.split()
        cmd = parts[0].upper()
        args = parts[1:]

        if cmd not in self.commands:
            self.send_response(conn, "ER Unknown command", addr)
            return

        try:
            self.commands[cmd](conn, args, addr)
        except Exception as e:
            error_msg = f"ER Application error: {e}"
            self.send_response(conn, error_msg, addr)

    def bank_code(self, conn, args, addr):
        """
        Sends the bank's IP address to the client.
        """
        self.send_response(conn, f"BC {self.get_my_ip()}", addr)

    def account_create(self, conn, args, addr):
        """
        Creates a new unique account number associated with the current bank IP.
        """
        ip = self.get_my_ip()

        with self.lock:
            accounts = load_accounts()

            while True:
                acc = random.randint(10000, 99999)
                key = f"{acc}/{ip}"
                if key not in accounts:
                    accounts[key] = 0
                    save_accounts(accounts)
                    self.send_response(conn, f"AC {key}", addr)
                    return

    def account_deposit(self, conn, args, addr):
        """
        Deposits a specified amount into an account.
        Forwards request if necessary.
        """
        if len(args) != 2:
            self.send_response(conn, "ER Bank account number and amount format is incorrect.", addr)
            return

        key, amount = args
        target_ip = key.split('/')[1]

        if target_ip != self.get_my_ip():
            res = self.forward_command(target_ip, f"AD {key} {amount}")
            self.send_response(conn, res, addr)
        else:
            try:
                amount = int(amount)
            except ValueError:
                self.send_response(conn, "ER Bank account number and amount format is incorrect.", addr)
                return

            with self.lock:
                accounts = load_accounts()

                if key not in accounts:
                    self.send_response(conn, "ER Account number format is incorrect.", addr)
                    return

                accounts[key] += amount
                save_accounts(accounts)

            self.send_response(conn, "AD", addr)

    def account_withdraw(self, conn, args, addr):
        """
        Withdraws a specified amount from an account.
        Forwards request if necessary.
        """
        if len(args) != 2:
            self.send_response(conn, "ER Bank account number and amount format is incorrect.", addr)
            return

        key, amount = args
        target_ip = key.split('/')[1]

        if target_ip != self.get_my_ip():
            res = self.forward_command(target_ip, f"AW {key} {amount}")
            self.send_response(conn, res, addr)
        else:
            try:
                amount = int(amount)
            except ValueError:
                self.send_response(conn, "ER Bank account number and amount format is incorrect.", addr)
                return

            with self.lock:
                accounts = load_accounts()

                if key not in accounts:
                    self.send_response(conn, "ER Account number format is incorrect.", addr)
                    return

                if accounts[key] < amount:
                    self.send_response(conn, "ER Insufficient funds.", addr)
                    return

                accounts[key] -= amount
                save_accounts(accounts)

            self.send_response(conn, "AW", addr)

    def account_balance(self, conn, args, addr):
        """
        Retrieves the balance of a specific account.
        Forwards request if necessary.
        """
        if len(args) != 1:
            self.send_response(conn, "ER Account number format is incorrect.", addr)
            return

        key = args[0]
        target_ip = key.split('/')[1]

        if target_ip != self.get_my_ip():
            res = self.forward_command(target_ip, f"AB {key}")
            self.send_response(conn, res, addr)
            return

        with self.lock:
            accounts = load_accounts()

            if key not in accounts:
                self.send_response(conn, "ER Account number format is incorrect.", addr)
                return

            self.send_response(conn, f"AB {accounts[key]}", addr)

    def account_remove(self, conn, args, addr):
        """
        Deletes a specific account if the balance is zero.
        """
        if len(args) != 1:
            self.send_response(conn, "ER Account number format is incorrect.", addr)
            return

        key = args[0]

        with self.lock:
            accounts = load_accounts()

            if key not in accounts:
                self.send_response(conn, "ER Account number format is incorrect.", addr)
                return

            if accounts[key] != 0:
                self.send_response(conn, "ER Cannot delete bank account containing funds.", addr)
                return

            del accounts[key]
            save_accounts(accounts)

        self.send_response(conn, "AR", addr)

    def bank_total(self, conn, args, addr):
        """
        Calculates and sends the total amount of money held in all accounts.
        """
        with self.lock:
            accounts = load_accounts()
            self.send_response(conn, f"BA {sum(accounts.values())}", addr)

    def bank_number(self, conn, args, addr):
        """
        Sends the total number of accounts managed by this bank.
        """
        with self.lock:
            accounts = load_accounts()
            self.send_response(conn, f"BN {len(accounts)}", addr)

    def get_my_ip(self):
        """
        Retrieves the local machine's IP address.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        except:
            return "127.0.0.1"
        finally:
            s.close()

    def forward_command(self, target_ip, command):
        """
        Attempts to forward a command to a target IP address.
        Scans a range of ports starting from BASE_PORT defined in config.
        Uses the P2P_TIMEOUT constant for socket operations.
        """
        for port in range(BASE_PORT, BASE_PORT + 11):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(P2P_TIMEOUT)
                    s.connect((target_ip, port))
                    s.sendall((command + "\r\n").encode())
                    response = s.recv(1024).decode().strip()
                    return response
            except (ConnectionRefusedError, socket.timeout):
                continue

        return "ER Bank unreachable"