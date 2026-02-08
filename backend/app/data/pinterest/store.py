from datetime import datetime
from typing import Optional, Dict, Any


_connection_state: Dict[str, Any] = {
    "connected": False,
    "connected_at": None,
    "access_token": None,
    "profile": None,
    "zep_user_id": None,
    "zep_thread_id": None,
}


def set_connected() -> None:
    _connection_state["connected"] = True
    _connection_state["connected_at"] = datetime.utcnow().isoformat() + "Z"


def set_disconnected() -> None:
    _connection_state["connected"] = False
    _connection_state["connected_at"] = None
    _connection_state["access_token"] = None
    _connection_state["profile"] = None
    _connection_state["zep_user_id"] = None
    _connection_state["zep_thread_id"] = None


def set_access_token(token: str) -> None:
    _connection_state["access_token"] = token


def set_profile(profile: Dict[str, Any]) -> None:
    _connection_state["profile"] = profile


def set_zep_user(user_id: str) -> None:
    _connection_state["zep_user_id"] = user_id


def set_zep_thread(thread_id: str) -> None:
    _connection_state["zep_thread_id"] = thread_id


def get_connection_status() -> Dict[str, Optional[str]]:
    return {
        "connected": bool(_connection_state["connected"]),
        "connected_at": _connection_state["connected_at"],
        "zep_user_id": _connection_state["zep_user_id"],
        "zep_thread_id": _connection_state["zep_thread_id"],
    }


def get_access_token() -> Optional[str]:
    return _connection_state["access_token"]


def get_profile() -> Optional[Dict[str, Any]]:
    return _connection_state["profile"]


def get_zep_user_id() -> Optional[str]:
    return _connection_state["zep_user_id"]


def get_zep_thread_id() -> Optional[str]:
    return _connection_state["zep_thread_id"]
