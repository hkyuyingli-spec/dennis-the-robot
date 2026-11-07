import json
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_data(filename):
    with (DATA_DIR / filename).open("r", encoding="utf-8") as source_file:
        return json.load(source_file)


def test_herbs_and_formulas_meet_minimum_counts_and_safety_metadata():
    entries = load_data("tcm_herbs_formulas.json")["entries"]
    herbs = [entry for entry in entries if entry.get("entry_type") == "herb"]
    formulas = [entry for entry in entries if entry.get("entry_type") == "formula"]

    assert len(herbs) >= 70
    assert len(formulas) >= 25
    assert all(
        entry.get("cautions_and_contraindications")
        and entry.get("pregnancy_safe") in (True, False, "consult_practitioner")
        for entry in entries
    )


def test_seasonal_foods_contains_all_four_seasons():
    seasons = load_data("seasonal_foods.json")["seasons"]

    assert {season["season"] for season in seasons} == {
        "spring", "summer", "autumn", "winter"
    }


def test_acupressure_has_at_least_fifteen_points_with_cautions():
    points = load_data("acupressure.json")["points"]

    assert len(points) >= 15
    assert all(point.get("cautions") for point in points)


def test_tcm_theory_covers_all_requested_frameworks():
    frameworks = load_data("tcm_theory.json")["frameworks"]

    assert {
        "eight_principles",
        "four_examinations",
        "six_stages",
        "four_levels",
    } <= {framework["id"] for framework in frameworks}
