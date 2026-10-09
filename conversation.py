"""Small, testable helpers for NutriBot chat history and prompt context."""
from __future__ import annotations

MAX_HISTORY_CHARS = 12000

def trim_history(messages: list[dict], max_chars: int = MAX_HISTORY_CHARS) -> list[dict]:
    """Keep the newest complete turns within a conservative character budget."""
    selected = []
    used = 0
    for message in reversed(messages):
        content = str(message.get("content", ""))
        if used + len(content) > max_chars:
            if not selected and message.get("role") == "user":
                content = content[-max_chars:]
                selected.append({"role": "user", "content": content})
            break
        selected.append({"role": message["role"], "content": content})
        used += len(content)
    selected.reverse()
    return selected

def build_system_prompt(personality: str, topic_context: str, language_directive: str, rag_context: str = "") -> str:
    return "\n\n".join(part for part in (personality, topic_context, language_directive, rag_context) if part)

def initialize_chat_state(state) -> None:
    state.setdefault("messages", [])
    state.setdefault("active_topic", None)
    state.setdefault("session_id", "")

def clear_chat_state(state) -> None:
    state["messages"] = []
    state["active_topic"] = None
    state.pop("prompt_trigger", None)
    state.pop("pending_topic_prompt", None)
