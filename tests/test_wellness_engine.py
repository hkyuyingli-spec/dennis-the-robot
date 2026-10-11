import pytest

from nutribot.wellness_engine import DISCLAIMER, WellnessEngine


def test_compute_state_maps_inputs_to_bounded_axes():
    state = WellnessEngine().compute_state(
        sleep_quality=80,
        stress=20,
        activity=60,
        diet_variety=90,
    )

    assert state == {"jing": 80, "qi": 60, "shen": 85}
    assert all(0 <= score <= 100 for score in state.values())


@pytest.mark.parametrize(
    "inputs",
    [
        (-1, 50, 50, 50),
        (50, 101, 50, 50),
        (float("nan"), 50, 50, 50),
        (50, float("inf"), 50, 50),
    ],
)
def test_compute_state_rejects_out_of_range_and_non_finite_values(inputs):
    with pytest.raises(ValueError):
        WellnessEngine().compute_state(*inputs)


def test_compute_state_rejects_non_numeric_values():
    with pytest.raises(TypeError):
        WellnessEngine().compute_state("good", 50, 50, 50)


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ({"jing": 20, "qi": 50, "shen": 60}, "sleep and wake schedule"),
        ({"jing": 60, "qi": 20, "shen": 50}, "150–300 minutes"),
        ({"jing": 60, "qi": 50, "shen": 20}, "stress-management practice"),
    ],
)
def test_recommendations_address_lowest_axis(state, expected):
    suggestions = WellnessEngine().recommend(state)

    assert len(suggestions) == 2
    assert any(expected in suggestion for suggestion in suggestions)
    assert all(isinstance(suggestion, str) for suggestion in suggestions)
    assert isinstance(DISCLAIMER, str)


def test_recommend_rejects_invalid_state():
    with pytest.raises(KeyError):
        WellnessEngine().recommend({"jing": 40, "qi": 50})
    with pytest.raises(ValueError):
        WellnessEngine().recommend({"jing": 40, "qi": 50, "shen": 120})
