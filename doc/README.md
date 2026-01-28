# P2P Banking System

**Authors:** Tony Menšík, Filip Pištěk

A decentralized peer-to-peer banking application written in pure Python. Unlike traditional banks, this system has no central server—every computer acts as both a client and a server. If you send money to an account hosted on another computer, the system automatically forwards the request to the correct peer in the network.

##  Key Features

* **P2P Architecture:** No central database. Each node manages its own `accounts.json`.
* **Smart Forwarding:** If you interact with a remote account (e.g., `12345/192.168.0.5`), the system automatically connects to that IP and processes the transaction.
* **Dual Interface:**
    * **GUI:** User-friendly window with tabs for **Logs** and **Commands**.
    * **Raw TCP:** Connect via PuTTY (Raw/Telnet) to port `65525`.
* **Robust Logging:** Tracks every request (`IN`) and response (`OUT`) with timestamps in `log/bank.log`.
* **Safety:** Uses `multiprocessing` and `RLock` to handle multiple connections safely without freezing.

##  How to Run

1.  **No installation required.** The app uses standard Python libraries.
2.  **Start the application:**

    ```bash
    py src/main.py
    ```

    *This starts the server in the background and opens the GUI.*

##  Commands (Protocol)

You can use these commands in the **GUI** or via **PuTTY**:

| Command | Example | Description |
| :--- | :--- | :--- |
| **BC** | `BC` | Get **B**ank **C**ode (My IP). |
| **AC** | `AC` | **A**ccount **C**reate (Returns ID/IP). |
| **AD** | `AD 12345/1.2.3.4 100` | **A**ccount **D**eposit money. |
| **AW** | `AW 12345/1.2.3.4 50` | **A**ccount **W**ithdraw money. |
| **AB** | `AB 12345/1.2.3.4` | **A**ccount **B**alance check. |
| **AR** | `AR 12345/1.2.3.4` | **A**ccount **R**emove (Delete). |
| **BA** | `BA` | **B**ank **A**mount (Total funds on node). |
| **BN** | `BN` | **B**ank **N**umber (Count of accounts). |

##  Configuration

Settings are stored in `config/config.json`:

```json
{
  "port": 65525,          // Server listening port
  "client_timeout": 60,   // Disconnect inactive clients (seconds)
  "p2p_timeout": 1.0      // Timeout for connecting to peers
}
```

##  Reused Code

* **User Interface (`src/ui.py`)**:
    * Source: [ItsTouny/projects - projekt_databaze](https://github.com/ItsTouny/projects/blob/main/projekt_databaze/src/main.py)
    * Description: The base structure of the Tkinter GUI and tab switching logic was adapted from this project.

* **Unit tests (`tests/unit_tests.py`)**:
    * Source: [FilipPistek - ImageBatchProcessor](https://github.com/FilipPistek/ImageBatchProcessor/blob/master/ImageBatchProcessorTests/FileValidatorTests.cs)
    * Description: Basic logic for making unit tests and converting code from C# to Python
