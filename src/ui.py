import tkinter as tk
from tkinter import ttk
import multiprocessing
import sys
import os
from command import Commands


class MockSocket:
    """
    Simulates a socket object to capture the response data sent by the Commands class.
    """

    def __init__(self):
        self.response = b""

    def sendall(self, data):
        """
        Captures the data sent by the command execution.
        """
        self.response += data

    def recv(self, size):
        """
        Returns empty bytes.
        """
        return b""

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class UI:
    """
    Graphical User Interface for the Bank Client with Tabs.
    Tab 1: Log Viewer.
    Tab 2: Command Execution.
    """

    def __init__(self, root):
        """
        Initializes the main window, tabs, and UI components.
        Uses RLock to prevent deadlocks when logging from GUI commands.
        """
        root.title("P2P Bank - Client (Direct)")
        root.geometry("650x300")
        root.protocol("WM_DELETE_WINDOW", self.shutdown)

        self.root = root
        self.lock = multiprocessing.RLock()
        self.commands = Commands(self.lock)

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill="both")

        self.tab_logs = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_logs, text="System Logs")
        self.setup_log_tab()

        self.tab_cmd = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_cmd, text="Execute Commands")
        self.setup_command_tab()

        self.refresh_logs()

    def setup_log_tab(self):
        """
        Sets up the widgets for the Log Viewer tab.
        Includes a text area for logs and buttons for Shutdown and Refresh.
        """
        frame_text = ttk.Frame(self.tab_logs)
        frame_text.pack(expand=True, fill="both", padx=10, pady=10)

        scrollbar = ttk.Scrollbar(frame_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_display = tk.Text(frame_text, height=10, width=80, yscrollcommand=scrollbar.set)
        self.log_display.pack(side=tk.LEFT, expand=True, fill="both")
        scrollbar.config(command=self.log_display.yview)

        frame_btns = ttk.Frame(self.tab_logs)
        frame_btns.pack(fill="x", padx=20, pady=10)

        tk.Button(frame_btns, text="Shutdown", command=self.shutdown).pack(side=tk.LEFT)
        tk.Button(frame_btns, text="Refresh Logs", command=self.refresh_logs).pack(side=tk.RIGHT)

    def setup_command_tab(self):
        """
        Sets up the widgets for the Command Execution tab.
        Uses absolute positioning within the tab frame.
        """
        self.cmd = ttk.Combobox(
            self.tab_cmd,
            values=["BC", "AC", "AD", "AW", "AB", "AR", "BA", "BN"],
            state="readonly"
        )
        self.cmd.current(0)
        self.cmd.place(x=20, y=20, width=120)
        self.cmd.bind("<<ComboboxSelected>>", self.update_fields)

        self.acc = tk.Entry(self.tab_cmd)
        self.slash = tk.Label(self.tab_cmd, text="/")
        self.ip = tk.Entry(self.tab_cmd)
        self.amount = tk.Entry(self.tab_cmd)

        self.output = tk.Text(self.tab_cmd, height=5, width=78)
        self.output.place(x=20, y=80)

        self.lbl_acc = tk.Label(self.tab_cmd, text="Account Number")
        self.lbl_ip = tk.Label(self.tab_cmd, text="IP Address")
        self.lbl_amt = tk.Label(self.tab_cmd, text="Amount")

        tk.Button(self.tab_cmd, text="Send", command=self.send).place(x=560, y=190)
        tk.Button(self.tab_cmd, text="Shutdown", command=self.shutdown).place(x=20, y=190)

        self.update_fields()

    def refresh_logs(self):
        """
        Reads the content of the log file and displays it in the log tab.
        """
        self.log_display.delete("1.0", tk.END)
        log_path = self.commands.log_file

        if not os.path.exists(log_path):
            self.log_display.insert(tk.END, "Log file not found yet.")
            return

        try:
            with open(log_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.log_display.insert(tk.END, content)
                self.log_display.see(tk.END)
        except Exception as e:
            self.log_display.insert(tk.END, f"Error reading log: {e}")

    def hide_all(self):
        """
        Removes all dynamic input fields and labels from the command view.
        """
        self.acc.place_forget()
        self.slash.place_forget()
        self.ip.place_forget()
        self.amount.place_forget()
        self.lbl_acc.place_forget()
        self.lbl_ip.place_forget()
        self.lbl_amt.place_forget()

    def update_fields(self, event=None):
        """
        Displays the appropriate input fields based on the selected command.
        """
        self.hide_all()
        c = self.cmd.get()
        x = 160
        y = 20

        if c in ["AB", "AR", "AD", "AW"]:
            self.acc.place(x=x, y=y, width=120)
            self.slash.place(x=x+125, y=y)
            self.ip.place(x=x+140, y=y, width=150)
            self.lbl_acc.place(x=x, y=y - 20)
            self.lbl_ip.place(x=x + 140, y=y - 20)

        if c in ["AD", "AW"]:
            self.amount.place(x=x + 300, y=y, width=100)
            self.lbl_amt.place(x=x + 300, y=y - 20)

    def send(self):
        """
        Constructs the command string from inputs and executes it via the Commands class.
        """
        c = self.cmd.get()
        acc = self.acc.get().strip()
        ip_val = self.ip.get().strip()
        amt = self.amount.get().strip()

        msg = ""
        if c in ["BC", "BA", "BN","AC"]:
            msg = c
        elif c in ["AB", "AR"]:
            msg = f"{c} {acc}/{ip_val}"
        elif c in ["AD", "AW"]:
            msg = f"{c} {acc}/{ip_val} {amt}"

        fake_conn = MockSocket()

        try:
            self.commands.execute(msg, fake_conn, addr="GUI")

            result_text = fake_conn.response.decode().strip()
            self.log_output(result_text)

        except Exception as e:
            self.log_output(f"ER Internal Error: {e}")

    def log_output(self, text):
        """
        Updates the output text area in the Command tab.
        """
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, text)

    def shutdown(self):
        """
        Closes the application window.
        """
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    UI(root)
    root.mainloop()