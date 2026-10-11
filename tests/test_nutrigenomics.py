import re

import pytest

from nutribot.nutrigenomics import (
    DISCLAIMER,
    NUTRIGENOMIC_MAP,
    recommend_from_markers,
)


def test_map_includes_required_markers_and_cited_cautious_entries():
    assert {"MTHFR", "COMT", "APOE4"} <= NUTRIGENOMIC_MAP.keys()
    for entry in NUTRIGENOMIC_MAP.values():
        assert set(entry) == {"supplement", "evidence_note", "citation_url"}
        assert entry["supplement"]
        assert entry["evidence_note"]
        assert entry["citation_url"].startswith("https://")


def test_recommend_from_markers_returns_fixed_schema_without_doses():
    results = recommend_from_markers({"mthfr": "C677T", "COMT": "Val/Met", "unknown": "x"})

    assert len(results) == 2
    for result in results:
        assert set(result) == {"supplement", "note", "citation_url", "disclaimer"}
        assert result["disclaimer"] == DISCLAIMER
        assert result["citation_url"].startswith("https://")
        assert not re.search(r"\b\d+\s*(?:mg|mcg|g|iu)\b", result["note"], re.I)


def test_marker_values_do_not_change_general_evidence_notes():
    first = recommend_from_markers({"APOE4": "positive"})
    second = recommend_from_markers({"APOE4": "negative"})

    assert first == second
    assert "No APOE4-specific" in first[0]["supplement"]


def test_unknown_markers_return_no_recommendations():
    assert recommend_from_markers({"unvalidated": "variant"}) == []


def test_marker_input_must_be_a_dict():
    with pytest.raises(TypeError):
        recommend_from_markers(["MTHFR"])
