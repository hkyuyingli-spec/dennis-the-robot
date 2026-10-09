from types import SimpleNamespace

from perf_logging import log_exception_safely, log_stream


def _chunk(content=None, *, usage=None, finish_reason=None):
    delta = SimpleNamespace(content=content, reasoning="internal reasoning")
    choice = SimpleNamespace(delta=delta, finish_reason=finish_reason)
    return SimpleNamespace(choices=[choice] if content is not None else [], usage=usage)


def test_stream_yields_only_text_and_reads_usage_from_final_chunk():
    usage = SimpleNamespace(prompt_tokens=23, completion_tokens=7, total_tokens=30)
    chunks = [
        _chunk(None),
        _chunk([{"type": "text", "text": "not a plain text delta"}]),
        _chunk("Hello"),
        SimpleNamespace(choices=[], usage=usage),
    ]
    state = {}

    result = list(log_stream(
        chunks,
        model="openai/gpt-oss-20b",
        request_id="test",
        prompt_tokens_estimate=20,
        started_at=0,
        state=state,
    ))

    assert result == ["Hello"]
    assert state["usage"]["prompt_tokens"] == 23
    assert state["usage"]["completion_tokens"] == 7
    assert state["usage"]["total_tokens"] == 30


def test_exception_diagnostic_keeps_traceback_but_redacts_sensitive_values(caplog):
    secret_message = "private user question"
    try:
        raise RuntimeError(f"request failed for {secret_message}")
    except RuntimeError as error:
        log_exception_safely(error, context="test", sensitive_values=[secret_message])

    diagnostic = caplog.text
    assert "RuntimeError" in diagnostic
    assert "Traceback" in diagnostic
    assert "private user question" not in diagnostic
    assert "[REDACTED]" in diagnostic
