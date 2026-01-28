import pytest
import sys
import os
import socket
import json
from unittest.mock import MagicMock, patch, mock_open

current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.abspath(os.path.join(current_dir, '..', 'src'))
sys.path.insert(0, src_path)

from src import main

CONFIG = {"port": 65525, "client_timeout": 60, "p2p_timeout": 1.0}
CLIENT_TIMEOUT = 60


@pytest.fixture
def mock_defaults(monkeypatch):
    """Fixture to set default values in the main module."""
    monkeypatch.setattr(main, "CONFIG", CONFIG, raising=False)
    monkeypatch.setattr(main, "CLIENT_TIMEOUT", CLIENT_TIMEOUT, raising=False)


# Tests for load_config
def test_load_config_file_not_exists(mock_defaults):
    """Test: File does not exist -> returns default CONFIG"""
    with patch('main.os.path.exists', return_value=False):
        result = main.load_config()
        assert result == CONFIG


def test_load_config_valid_file(mock_defaults):
    """Test: File exists and is valid -> returns merged configuration"""
    mock_data = json.dumps({"port": 65525})

    with patch('main.os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data=mock_data)):
            result = main.load_config()
            expected = CONFIG.copy()
            expected["port"] = 65525
            assert result == expected


def test_load_config_invalid_json(mock_defaults):
    """Test: File exists but is corrupt JSON -> returns default CONFIG"""
    with patch('main.os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data="{invalid_json")):
            result = main.load_config()
            assert result == CONFIG


# Tests for handle_client
def test_handle_client_socket_timeout(mock_defaults):
    """Test: Timeout occurs while waiting for data"""
    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.recv.side_effect = socket.timeout

    addr = ("0.0.0.0", 65525)
    lock = MagicMock()

    with patch('main.Commands'):
        main.handle_client(mock_conn, addr, lock)

        assert mock_conn.sendall.called
        args, _ = mock_conn.sendall.call_args
        assert b"TIMEOUT" in args[0]


def test_handle_client_connection_reset(mock_defaults):
    """Test: Client resets connection"""
    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.recv.side_effect = ConnectionResetError

    addr = ("0.0.0.0", 65525)
    lock = MagicMock()

    with patch('main.Commands'):
        main.handle_client(mock_conn, addr, lock)

        mock_conn.sendall.assert_not_called()