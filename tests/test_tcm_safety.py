import json
from pathlib import Path

from backend.chat import answer_chat


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_data(filename):
    with (DATA_DIR / filename).open("r", encoding="utf-8") as source_file:
        return json.load(source_file)


def test_pregnancy_restricted_acupressure_points_are_blocked_before_model_call():
    for code in ("LI4", "SP6", "GB21"):
        provider_called = False

        def get_client():
            nonlocal provider_called
            provider_called = True
            raise AssertionError("pregnancy-restricted point must not reach the model")

        response = answer_chat(
            messages=[{
                "role": "user",
                "content": f"I am pregnant. Is it safe to stimulate {code}?",
            }],
            language="en",
            get_client=get_client,
            wrap_client=lambda client, _language: client,
        )

        assert "during pregnancy" in response["reply"]
        assert provider_called is False


def test_herb_marked_unsafe_in_pregnancy_is_not_sent_to_model(monkeypatch):
    unsafe_herb = {
        "id": "test_botanical",
        "category": "single_herb",
        "name_english": "Test Botanical",
        "name_chinese": "",
        "pinyin": "",
        "pregnancy_safe": False,
    }
    monkeypatch.setattr(
        "backend.chat._load_knowledge",
        lambda: ([], [unsafe_herb], [], [], [], []),
    )
    provider_called = False

    def get_client():
        nonlocal provider_called
        provider_called = True
        raise AssertionError("pregnancy-unsafe herb must not reach the model")

    response = answer_chat(
        messages=[{
            "role": "user",
            "content": "I am pregnant. Can I use Test Botanical?",
        }],
        language="en",
        get_client=get_client,
        wrap_client=lambda client, _language: client,
    )

    assert "during pregnancy" in response["reply"]
    assert provider_called is False


def test_all_formula_records_include_cautions():
    entries = load_data("tcm_herbs_formulas.json")["entries"]
    formulas = [entry for entry in entries if entry.get("entry_type") == "formula"]

    assert formulas
    assert all(entry.get("cautions_and_contraindications") for entry in formulas)
