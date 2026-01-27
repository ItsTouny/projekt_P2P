import json
import os

# The name of the configuration file
CONFIG_FILENAME = "config.json"


def load_config():
    """
    Loads TCP connection settings from config.json.
    Returns a dictionary with PORT, IP, and timeout.
    """
    # Default values in case the file is missing
    defaults = {
        "PORT": 65525,
        "timeout": 5
    }

    # Check if file exists
    if not os.path.exists(CONFIG_FILENAME):
        print(f"[WARN] {CONFIG_FILENAME} not found. Using default settings.")
        return defaults

    try:
        with open(CONFIG_FILENAME, 'r') as f:
            data = json.load(f)

            # Safely get values (use defaults if keys are missing)
            config = {
                "PORT": data.get("PORT", defaults["PORT"]),
                "timeout": data.get("timeout", defaults["timeout"])
            }
            return config

    except json.JSONDecodeError:
        print(f"[ERR] {CONFIG_FILENAME} is not valid JSON. Using defaults.")
        return defaults
    except Exception as e:
        print(f"[ERR] Could not load config: {e}. Using defaults.")
        return defaults