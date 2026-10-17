from types import SimpleNamespace

from fastapi.testclient import TestClient
from groq import APIStatusError
from httpx import Request, Response

from backend.main import _agent_client_with_policy, _allow_request, app


client = TestClient(app)


def test_health_endpoint_is_available_without_provider_credentials():
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_request_rejects_unsupported_language():
    response = client.post(
        "/api/v1/chat",
        json={
            "language": "fr",
            "messages": [{"role": "user", "content": "Hello"}],
        },
    )

    assert response.status_code == 422


def test_chat_request_rejects_non_user_final_message():
    response = client.post(
        "/api/v1/chat",
        json={
            "language": "en",
            "messages": [{"role": "assistant", "content": "Hello"}],
        },
    )

    assert response.status_code == 422


def test_emergency_request_redirects_without_provider_credentials():
    response = client.post(
        "/api/v1/chat",
        json={
            "language": "en",
            "messages": [{"role": "user", "content": "I'm having chest pain"}],
        },
    )

    assert response.status_code == 200
    assert "own health situation" in response.json()["reply"]


def test_capacitor_origin_is_allowed():
    response = client.get(
        "/api/v1/health",
        headers={"Origin": "https://localhost"},
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://localhost"


def test_capacitor_chat_preflight_allows_json_post():
    response = client.options(
        "/api/v1/chat",
        headers={
            "Origin": "capacitor://localhost",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "capacitor://localhost"
    assert "POST" in response.headers["access-control-allow-methods"]
    assert "content-type" in response.headers["access-control-allow-headers"].lower()


def test_chat_reports_missing_provider_configuration_as_503(monkeypatch):
    def missing_provider(**_options):
        raise RuntimeError("GROQ_API_KEY is not configured on the backend")

    monkeypatch.setattr("backend.main.answer_chat", missing_provider)

    response = client.post(
        "/api/v1/chat",
        json={
            "language": "en",
            "messages": [{"role": "user", "content": "Suggest a simple wellness habit"}],
        },
    )

    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]


def test_chat_reports_provider_failure_as_502(monkeypatch):
    def provider_failure(**_options):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr("backend.main.answer_chat", provider_failure)

    response = client.post(
        "/api/v1/chat",
        json={
            "language": "en",
            "messages": [{"role": "user", "content": "Suggest a simple wellness habit"}],
        },
    )

    assert response.status_code == 502
    assert "could not complete" in response.json()["detail"]


def test_per_ip_rate_limit_resets_after_its_window():
    ip = "test-rate-limit-client"

    assert all(_allow_request(ip, now=0) for _ in range(20))
    assert _allow_request(ip, now=1) is False
    assert _allow_request(ip, now=60) is True


def test_provider_policy_and_fallback_are_applied(monkeypatch):
    monkeypatch.setenv("GROQ_MODEL_FALLBACK", "configured/fallback")
    failed_response = Response(
        429,
        request=Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
    )
    rate_limit = APIStatusError("rate limited", response=failed_response, body=None)
    calls = []

    def create_completion(**options):
        calls.append(options)
        if len(calls) == 1:
            raise rate_limit
        return "fallback response"

    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=create_completion)
        )
    )
    wrapped = _agent_client_with_policy(client, "en")

    result = wrapped.chat.completions.create(
        model="configured/primary",
        messages=[
            {"role": "system", "content": "Specialist instructions"},
            {"role": "user", "content": "A wellness question"},
        ],
    )

    assert result == "fallback response"
    assert [call["model"] for call in calls] == [
        "configured/primary",
        "configured/fallback",
    ]
    assert "educational wellness assistant" in calls[0]["messages"][0]["content"]
