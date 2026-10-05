import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


class StatusError(Exception):
    def __init__(self, status_code):
        super().__init__(f"mock status {status_code}")
        self.status_code = status_code


class MockAPIConnectionError(Exception):
    pass


class MockAPITimeoutError(MockAPIConnectionError):
    pass


class MockRateLimitError(StatusError):
    pass


class FakeSecrets(dict):
    def get(self, key, default=None):
        return super().get(key, default)


def load_app_helpers(settings=None, responses=(), environment=None):
    source = APP_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    helper_names = {
        "get_setting", "GroqAuthenticationFailure", "GroqInvalidRequestFailure",
        "_groq_status_code", "_raise_clear_groq_error", "_request_groq_completion",
        "create_groq_completion",
    }
    nodes = [
        node for node in tree.body
        if (isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in helper_names)
        or (isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id in {"MODEL_PRIMARY", "MODEL_FALLBACK"}
            for target in node.targets
        ))
    ]
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
        create=Mock(side_effect=list(responses))
    )))
    fake_os = SimpleNamespace(getenv=lambda key: (environment or {}).get(key))
    namespace = {
        "os": fake_os,
        "st": SimpleNamespace(secrets=FakeSecrets(settings or {})),
        "client": client,
        "APIConnectionError": MockAPIConnectionError,
        "APITimeoutError": MockAPITimeoutError,
    }
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(APP_PATH), "exec"), namespace)
    return namespace, client, source


def invoke(namespace, messages=None, **kwargs):
    options = {"max_tokens": 900, "temperature": 0.7, "stream": True}
    options.update(kwargs)
    return namespace["create_groq_completion"](
        messages=messages or [{"role": "user", "content": "mock input"}],
        **options,
    )


def test_primary_429_uses_fallback_and_returns_answer(capsys):
    answer = object()
    namespace, client, _ = load_app_helpers(responses=[MockRateLimitError(429), answer])
    assert invoke(namespace) is answer
    calls = client.chat.completions.create.call_args_list
    assert [call.kwargs["model"] for call in calls] == [namespace["MODEL_PRIMARY"], namespace["MODEL_FALLBACK"]]
    assert "[groq] primary openai/gpt-oss-20b failed (429), using fallback qwen/qwen3.8-27b" in capsys.readouterr().out


@pytest.mark.parametrize("status", [404, 500, 503])
def test_not_found_and_server_errors_use_fallback(status):
    answer = object()
    namespace, client, _ = load_app_helpers(responses=[StatusError(status), answer])
    assert invoke(namespace) is answer
    assert client.chat.completions.create.call_count == 2


def test_timeout_uses_fallback():
    answer = object()
    namespace, client, _ = load_app_helpers(responses=[MockAPITimeoutError("timeout"), answer])
    assert invoke(namespace) is answer
    assert client.chat.completions.create.call_count == 2


@pytest.mark.parametrize("status", [400, 401, 403])
def test_bad_request_and_auth_errors_do_not_use_fallback(status):
    namespace, client, _ = load_app_helpers(responses=[StatusError(status)])
    error_type = namespace["GroqInvalidRequestFailure"] if status == 400 else namespace["GroqAuthenticationFailure"]
    with pytest.raises(error_type, match="Groq"):
        invoke(namespace)
    client.chat.completions.create.assert_called_once()


def test_both_models_rate_limited_propagates_rate_limit():
    namespace, client, _ = load_app_helpers(responses=[MockRateLimitError(429), MockRateLimitError(429)])
    with pytest.raises(MockRateLimitError):
        invoke(namespace)
    assert client.chat.completions.create.call_count == 2


def test_rate_limit_handlers_show_existing_recharging_message():
    source = APP_PATH.read_text(encoding="utf-8")
    message = "NutriBot is recharging its Qi. Please return in a few moments."
    assert source.count("except RateLimitError:") >= 3
    assert source.count(message) >= 3


def test_same_primary_and_fallback_skips_duplicate_request():
    namespace, client, _ = load_app_helpers(responses=[StatusError(404)])
    namespace["MODEL_FALLBACK"] = namespace["MODEL_PRIMARY"]
    with pytest.raises(StatusError):
        invoke(namespace)
    client.chat.completions.create.assert_called_once()


@pytest.mark.parametrize(
    "model,expect_reasoning",
    [("openai/gpt-oss-20b", True), ("openai/gpt-oss-120b", True), ("qwen/qwen3.8-27b", False), ("some/other-model", False)],
)
def test_reasoning_effort_only_for_gpt_oss_models(model, expect_reasoning):
    namespace, client, _ = load_app_helpers(responses=[object()])
    namespace["MODEL_PRIMARY"] = model
    invoke(namespace)
    kwargs = client.chat.completions.create.call_args.kwargs
    assert ("reasoning_effort" in kwargs) is expect_reasoning
    if expect_reasoning:
        assert kwargs["reasoning_effort"] == "low"


def test_model_settings_are_configurable_and_have_defaults():
    namespace, _, _ = load_app_helpers()
    assert namespace["MODEL_PRIMARY"] == "openai/gpt-oss-20b"
    assert namespace["MODEL_FALLBACK"] == "qwen/qwen3.8-27b"

    namespace, _, _ = load_app_helpers(settings={
        "GROQ_MODEL": "custom/primary",
        "GROQ_MODEL_FALLBACK": "custom/fallback",
    })
    assert namespace["MODEL_PRIMARY"] == "custom/primary"
    assert namespace["MODEL_FALLBACK"] == "custom/fallback"

    namespace, _, _ = load_app_helpers(
        settings={"GROQ_MODEL": "secret/primary", "GROQ_MODEL_FALLBACK": "secret/fallback"},
        environment={"GROQ_MODEL": "env/primary"},
    )
    assert namespace["MODEL_PRIMARY"] == "env/primary"
    assert namespace["MODEL_FALLBACK"] == "secret/fallback"


def test_quantum_insights_uses_shared_helper_and_can_fallback():
    answer = object()
    namespace, client, source = load_app_helpers(responses=[StatusError(404), answer])
    quantum_source = source[source.index("# AI Explanation using Groq"):]
    assert "explanation_response = create_groq_completion(" in quantum_source
    assert "max_tokens=900" in quantum_source
    assert "stream=False" in quantum_source
    quantum_call = quantum_source.split("explanation_response = create_groq_completion(", 1)[1].split("\n                    )", 1)[0]
    assert "temperature=" not in quantum_call
    assert invoke(
        namespace,
        messages=[{"role": "user", "content": "Quantum Insights"}],
        temperature=None,
        stream=False,
    ) is answer
    assert client.chat.completions.create.call_count == 2
    for call in client.chat.completions.create.call_args_list:
        assert call.kwargs["stream"] is False
        assert "temperature" not in call.kwargs


def test_all_app_call_paths_share_one_fallback_helper():
    source = APP_PATH.read_text(encoding="utf-8")
    assert source.count("client.chat.completions.create(") == 1
    assert source.count("= create_groq_completion(") == 3


def test_retired_qwen_name_absent_from_app_and_red_flag_script():
    app_source = APP_PATH.read_text(encoding="utf-8")
    red_flag_source = (APP_PATH.parent / "scripts/test_red_flag_pipeline.py").read_text(encoding="utf-8")
    assert "qwen3.6" not in app_source
    assert "qwen3.6" not in red_flag_source
