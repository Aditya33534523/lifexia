from __future__ import annotations

from collections import defaultdict
from datetime import datetime
import itertools
import uuid


_conversation_id_counter = itertools.count(1)
# user_email -> [{id, session_id, created_at, messages:[{role,content,timestamp}]}]
_conversations_by_user: dict[str, list[dict]] = defaultdict(list)
# session_id -> (user_email, conversation)
_session_index: dict[str, tuple[str, dict]] = {}


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _new_session_id() -> str:
    return f"session_{uuid.uuid4().hex}"


def get_or_create_conversation(user_email: str, session_id: str | None = None) -> dict:
    if session_id and session_id in _session_index:
        return _session_index[session_id][1]

    conversation = {
        "id": next(_conversation_id_counter),
        "session_id": session_id or _new_session_id(),
        "created_at": _now_iso(),
        "messages": [],
    }
    _conversations_by_user[user_email].insert(0, conversation)
    _session_index[conversation["session_id"]] = (user_email, conversation)
    return conversation


def append_message(user_email: str, role: str, content: str, session_id: str | None = None) -> dict:
    conversation = get_or_create_conversation(user_email, session_id)
    conversation["messages"].append(
        {
            "role": role,
            "content": content,
            "timestamp": _now_iso(),
        }
    )
    return conversation


def list_history(user_email: str) -> list[dict]:
    conversations = _conversations_by_user.get(user_email, [])
    history = []
    for conv in conversations:
        messages = conv["messages"]
        last_message = messages[-1]["content"] if messages else "No messages"
        title = messages[0]["content"][:40] if messages else "Untitled Chat"
        history.append(
            {
                "id": conv["id"],
                "session_id": conv["session_id"],
                "title": title,
                "last_message": last_message,
                "created_at": conv["created_at"],
            }
        )
    return history


def get_conversation(session_id: str) -> dict | None:
    entry = _session_index.get(session_id)
    if not entry:
        return None
    return entry[1]


def delete_conversation(conversation_id: int) -> bool:
    for user_email, conversations in _conversations_by_user.items():
        for index, conv in enumerate(conversations):
            if conv["id"] == conversation_id:
                conversations.pop(index)
                _session_index.pop(conv["session_id"], None)
                return True
    return False
