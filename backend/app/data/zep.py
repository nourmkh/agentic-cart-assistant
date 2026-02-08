import os
import uuid
from typing import Optional

from zep_cloud.client import Zep
from zep_cloud.types import Message


def get_zep_client() -> Optional[Zep]:
    api_key = os.environ.get("ZEP_API_KEY")
    if not api_key:
        return None
    return Zep(api_key=api_key)


def ensure_zep_user(client: Zep, user_id: str, email: Optional[str] = None, first_name: Optional[str] = None,
                    last_name: Optional[str] = None) -> None:
    try:
        client.user.get(user_id=user_id)
    except Exception:
        client.user.add(
            user_id=user_id,
            email=email,
            first_name=first_name or "Pinterest",
            last_name=last_name or "User",
        )


def ensure_zep_thread(client: Zep, user_id: str, thread_id: Optional[str] = None) -> str:
    thread_id = thread_id or f"pinterest-{user_id}-{uuid.uuid4().hex[:8]}"
    try:
        client.thread.get(thread_id=thread_id)
    except Exception:
        client.thread.create(thread_id=thread_id, user_id=user_id)
    return thread_id


def add_message_to_thread(client: Zep, thread_id: str, message: Message) -> None:
    client.thread.add_messages(thread_id=thread_id, messages=[message])
