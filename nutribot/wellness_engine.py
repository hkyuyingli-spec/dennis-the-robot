"""Simple lifestyle scoring based on sleep, activity, stress, and diet variety."""
from __future__ import annotations

import math
from numbers import Real


DISCLAIMER = "This is educational information, not medical advice."


def _score_input(name: str, value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a numeric value from 0 to 100")
    score = float(value)
    if not math.isfinite(score) or not 0 <= score <= 100:
        raise ValueError(f"{name} must be finite and between 0 and 100")
    return score


class WellnessEngine:
    """Map self-reported lifestyle measures to bounded wellness axes."""

    def compute_state(
        self,
        sleep_quality: float,
        stress: float,
        activity: float,
        diet_variety: float,
    ) -> dict:
        sleep = _score_input("sleep_quality", sleep_quality)
        stress_score = _score_input("stress", stress)
        activity_score = _score_input("activity", activity)
        diet_score = _score_input("diet_variety", diet_variety)

        return {
            "jing": round(sleep),
            "qi": round(activity_score),
            "shen": round(((100 - stress_score) + diet_score) / 2),
        }

    def recommend(self, state: dict) -> list[str]:
        """Return cautious lifestyle and supplement considerations for the lowest axis."""
        if not isinstance(state, dict):
            raise TypeError("state must be a dict containing the three wellness scores")

        scores = {
            axis: _score_input("wellness score", state[axis])
            for axis in ("jing", "qi", "shen")
        }
        lowest_axis = min(scores, key=scores.get)

        recommendations = {
            "jing": [
                "Keep a consistent sleep and wake schedule, allow enough time for sleep, and reduce late-day caffeine and bright evening light; seek assessment for persistent insomnia or loud snoring.",
                "If sleep timing remains difficult, discuss whether melatonin is appropriate with a clinician or pharmacist; it is not suitable for everyone and can interact with medicines.",
            ],
            "qi": [
                "Increase activity gradually toward 150–300 minutes of moderate aerobic activity weekly, plus muscle-strengthening activity on at least two days, adapted to your ability.",
                "Prioritize adequate food, protein, and hydration. Creatine monohydrate may support strength when paired with resistance training, but discuss it with a clinician first if you have kidney disease or take medicines.",
            ],
            "shen": [
                "Try a regular stress-management practice such as mindfulness, slow breathing, or time with supportive people; seek professional support if distress persists.",
                "Favor a varied diet that includes fish or other sources of omega-3 fats. Supplement benefits vary; discuss an omega-3 supplement with a clinician or pharmacist if you have a relevant dietary or clinical reason, especially when taking medicines.",
            ],
        }
        return recommendations[lowest_axis]
