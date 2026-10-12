import json
import re
from pathlib import Path

from conversation import build_system_prompt
from nutribot.classics import (
    find_passages,
    get_disclaimer,
    get_translations_note,
    load_waijing,
)


DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "classics"
    / "waijing.json"
)


def test_load_waijing_returns_document_metadata_and_passages():
    document = load_waijing()

    assert isinstance(document, dict)
    assert {
        "title", "author", "source", "authenticity_note",
        "translations_note", "passages",
    } <= document.keys()
    assert document["passages"]


def test_every_passage_has_required_fields():
    document = load_waijing()

    assert 20 <= len(document["passages"]) <= 30
    assert all(
        set(passage) == {"id", "theme", "text_zh", "text_en"}
        for passage in document["passages"]
    )
    assert all(
        re.fullmatch(
            r"[\u3400-\u4dbf\u4e00-\u9fff，。！？：；、（）《》「」“”‘’]+",
            passage["text_zh"],
        )
        for passage in document["passages"]
    )
    assert all(
        re.fullmatch(r"[\x00-\x7f]+", passage["text_en"])
        for passage in document["passages"]
    )
    assert all(
        20 <= len(passage["text_en"].split()) <= 100
        for passage in document["passages"]
    )
    assert all(
        15 <= len(passage["text_zh"]) <= 80
        for passage in document["passages"]
    )


def test_find_passages_matches_seasonal_living():
    matches = find_passages("seasonal living")

    assert matches
    assert all(
        set(passage) == {"id", "theme", "text_zh", "text_en"}
        for passage in matches
    )
    assert find_passages("四季")


def test_unrelated_query_has_no_matches():
    assert find_passages("random unrelated string xyz") == []


def test_stopword_only_or_unrelated_query_returns_no_matches():
    assert find_passages("how do I install python on windows") == []
    assert find_passages("what is the weather today") == []
    assert find_passages("tell me a story") == []


def test_meaningful_query_still_matches():
    assert find_passages("seasonal living balance")
    assert find_passages("winter health")
    assert find_passages("四季")


def test_get_disclaimer_returns_authenticity_note():
    assert get_disclaimer() == load_waijing()["authenticity_note"]


def test_get_translations_note_returns_document_note():
    assert get_translations_note() == load_waijing()["translations_note"]


def test_json_excludes_forbidden_themes():
    content = DATA_PATH.read_text(encoding="utf-8").casefold()

    assert "內丹" not in content
    assert "房中" not in content
    assert "internal alchemy" not in content


def test_json_file_is_valid():
    with DATA_PATH.open(encoding="utf-8") as source_file:
        assert isinstance(json.load(source_file), dict)


def test_system_prompt_labels_classical_excerpts_as_non_clinical():
    reference = ["[wj-001 | seasonal_balance] seasonal excerpt"]

    prompt = build_system_prompt(
        "Base policy",
        "",
        "Reply in English.",
        classical_reference=reference,
        classical_disclaimer=get_disclaimer(),
    )

    assert (
        "The following excerpts are from the Qing-era text Waijing Weiyan, "
        "a traditional philosophy document. Present them as traditional "
        "philosophy, not clinical advice."
    ) in prompt
    assert get_disclaimer() in prompt
    assert reference[0] in prompt


def test_chat_handler_searches_classics_before_invoking_agent():
    app_source = (
        Path(__file__).resolve().parent.parent / "app.py"
    ).read_text(encoding="utf-8")
    search_position = app_source.index(
        "classical_passages = find_passages(current_user_prompt, max_matches=2)"
    )
    agent_position = app_source.index("AgentOrchestrator(", search_position)

    assert search_position < agent_position
