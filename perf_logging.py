"""Privacy-preserving Groq usage and prompt-part instrumentation."""
from __future__ import annotations

import logging
import json
import re
import time
import traceback
from typing import Iterable

logger = logging.getLogger("nutribot.performance")


def log_exception_safely(error: BaseException, *, context: str, sensitive_values=()) -> None:
    """Log exception details and traceback after removing credentials and prompt text."""
    text_to_redact = [str(value) for value in sensitive_values if value]
    # Also remove the configured key if an HTTP/client exception includes it.
    try:
        import os
        key = os.getenv("GROQ_API_KEY")
        if key:
            text_to_redact.append(key)
    except Exception:
        pass
    try:
        import streamlit as st
        key = st.secrets.get("GROQ_API_KEY")
        if key:
            text_to_redact.append(str(key))
    except Exception:
        pass

    message = str(error)
    stack = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    redactions = set(text_to_redact)
    redactions.update(json.dumps(value, ensure_ascii=False)[1:-1] for value in text_to_redact)
    for secret in sorted(redactions, key=len, reverse=True):
        message = message.replace(secret, "[REDACTED]")
        stack = stack.replace(secret, "[REDACTED]")
    logger.error("%s exception_type=%s message=%s\n%s", context, type(error).__name__, message, stack)


def approximate_tokens(text: str) -> int:
    """Conservative rough estimate for monitoring only; never log the text."""
    value = text or ""
    cjk = len(re.findall(r"[\u3400-\u9fff]", value))
    other = max(0, len(value) - cjk)
    return max(0, cjk + (other + 3) // 4)


def log_prompt_parts(parts: dict[str, str], *, request_id: str) -> dict[str, int]:
    counts = {name: approximate_tokens(value) for name, value in parts.items()}
    total = sum(counts.values())
    shares = {name: round((count / total) * 100, 1) if total else 0 for name, count in counts.items()}
    logger.info("groq_prompt_parts request_id=%s approx_tokens=%s shares_pct=%s", request_id, counts, shares)
    return counts


def _usage_value(usage, key: str):
    if usage is None:
        return None
    if isinstance(usage, dict):
        return usage.get(key)
    return getattr(usage, key, None)


def log_stream(chunks: Iterable, *, model: str, request_id: str, prompt_tokens_estimate: int,
               started_at: float, state: dict | None = None, sensitive_values=()):
    """Yield content strings while logging usage/timing when the stream ends."""
    state = state if state is not None else {}
    first_token_ms = None
    usage = None
    try:
        for chunk in chunks:
            chunk_usage = getattr(chunk, "usage", None)
            if chunk_usage is not None:
                usage = chunk_usage
            choices = getattr(chunk, "choices", None) or []
            if not choices:
                continue
            choice = choices[0]
            finish_reason = getattr(choice, "finish_reason", None)
            if finish_reason:
                state["finish_reason"] = finish_reason
            delta = getattr(choice, "delta", None)
            content = getattr(delta, "content", None) if delta is not None else None
            # Ignore reasoning/non-text deltas; Streamlit's write_stream and
            # cached string assembly both require text chunks.
            if isinstance(content, str) and content:
                if first_token_ms is None:
                    first_token_ms = round((time.perf_counter() - started_at) * 1000, 1)
                yield content
    except Exception as error:
        log_exception_safely(error, context=f"groq_stream request_id={request_id}", sensitive_values=sensitive_values)
        raise
    finally:
        total_ms = round((time.perf_counter() - started_at) * 1000, 1)
        prompt_tokens = _usage_value(usage, "prompt_tokens")
        completion_tokens = _usage_value(usage, "completion_tokens")
        total_tokens = _usage_value(usage, "total_tokens")
        logger.info(
            "groq_request request_id=%s model=%s prompt_tokens=%s completion_tokens=%s total=%s total_tokens=%s prompt_estimate=%s first_token_ms=%s total_ms=%s",
            request_id, model, prompt_tokens, completion_tokens, total_tokens,
            total_tokens, prompt_tokens_estimate, first_token_ms, total_ms,
        )
        state["usage"] = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "prompt_estimate": prompt_tokens_estimate,
            "first_token_ms": first_token_ms,
            "total_ms": total_ms,
        }


def log_nonstream(*, model: str, request_id: str, usage, prompt_tokens_estimate: int, started_at: float):
    total_ms = round((time.perf_counter() - started_at) * 1000, 1)
    prompt_tokens = _usage_value(usage, "prompt_tokens")
    completion_tokens = _usage_value(usage, "completion_tokens")
    total_tokens = _usage_value(usage, "total_tokens")
    logger.info(
        "groq_request request_id=%s model=%s prompt_tokens=%s completion_tokens=%s total=%s total_tokens=%s prompt_estimate=%s first_token_ms=%s total_ms=%s",
        request_id, model, prompt_tokens, completion_tokens, total_tokens,
        total_tokens, prompt_tokens_estimate, total_ms, total_ms,
    )
