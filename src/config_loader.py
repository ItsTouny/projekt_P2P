import json
import os

DEFAULT_CONFIG = {
    "port": 65525,
    "client_timeout": 60,
    "p2p_timeout": 1.0
}


def load_config():
    """
    Loads configuration settings from a JSON file located in the '../config' directory.
    If the file does not exist or is invalid, returns default values.

    Returns:
        dict: A dictionary containing configuration parameters (port, client_timeout, p2p_timeout).
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "config.json")

    if not os.path.exists(config_path):
        return DEFAULT_CONFIG

    try:
        with open(config_path, "r") as f:
            config = json.load(f)
            return {**DEFAULT_CONFIG, **config}
    except Exception:
        return DEFAULT_CONFIG