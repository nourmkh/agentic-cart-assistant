from datetime import datetime
from typing import Optional, Dict, Any


_connection_state: Dict[str, Any] = {
    "connected": False,
    "connected_at": None,
}


def set_connected() -> None:
    _connection_state["connected"] = True
    _connection_state["connected_at"] = datetime.utcnow().isoformat() + "Z"


def set_disconnected() -> None:
    _connection_state["connected"] = False
    _connection_state["connected_at"] = None


def get_connection_status() -> Dict[str, Optional[str]]:
    return {
        "connected": bool(_connection_state["connected"]),
        "connected_at": _connection_state["connected_at"],
    }
