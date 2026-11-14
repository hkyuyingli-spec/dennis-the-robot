"""Small, offline helpers for draft herbal kitchen content."""

import json
import re
from pathlib import Path
from typing import Any, Mapping


CAUTION_TEXT = (
    "For general food education only. Herbs may cause allergies or interact with "
    "medicines. This information is not medical advice; consult a qualified health "
    "professional about personal health concerns."
)

BANNED_WORDS = (
    "cure",
    "cures",
    "cured",
    "treat",
    "treats",
    "treatment",
    "heal",
    "heals",
    "healing",
    "prevent",
    "prevents",
    "prevention",
)


def load_data() -> dict[str, Any]:
    """Load the local herbal kitchen JSON data file."""
    path = Path(__file__).resolve().parent.parent / "data" / "herbal_kitchen.json"
    with path.open(encoding="utf-8") as data_file:
        return json.load(data_file)


def published_herbs() -> list[dict[str, Any]]:
    """Return only herb records explicitly marked published."""
    return [herb for herb in load_data().get("herbs", [])
            if herb.get("status") == "published"]


def build_prompt(dish: str, options: Mapping[str, Any] | None) -> str:
    """Build a constrained, educational prompt for a dish suggestion."""
    opts = dict(options or {})
    allowed = [herb.get("name", "") for herb in published_herbs() if herb.get("name")]
    allowed_text = ", ".join(allowed) if allowed else "none"
    return (
        "Suggest a food-focused dish using only the allowed herbs listed below. "
        "Do not make disease, treatment, cure, prevention, or guaranteed-effect claims. "
        f"Dish: {dish}\nOptions: {json.dumps(opts, ensure_ascii=False, sort_keys=True)}\n"
        f"Allowed published herbs: {allowed_text}\n{CAUTION_TEXT}"
    )


def validate_output(output: Any, allowed_herbs: list[str] | tuple[str, ...] | set[str]) -> bool:
    """Return False for unapproved herb names or banned medical-claim words.

    Structured results can provide an ``herbs`` list and text/content fields. For
    plain text, herb names are checked when they follow an explicit ``Herbs:`` label.
    """
    if isinstance(output, Mapping):
        herbs = output.get("herbs", [])
        if isinstance(herbs, str):
            herbs = [part.strip() for part in herbs.split(",") if part.strip()]
        if not isinstance(herbs, (list, tuple, set)):
            return False
        allowed = {str(name).casefold() for name in allowed_herbs}
        if any(str(herb).casefold() not in allowed for herb in herbs):
            return False
        text = " ".join(str(output.get(key, "")) for key in ("text", "content", "description"))
    else:
        text = str(output)
        allowed = {str(name).casefold() for name in allowed_herbs}
        match = re.search(r"\bherbs?\s*:\s*([^\n.;]+)", text, re.IGNORECASE)
        if match:
            named_herbs = [name.strip() for name in match.group(1).split(",") if name.strip()]
            if any(name.casefold() not in allowed for name in named_herbs):
                return False

    banned_pattern = r"\b(?:" + "|".join(re.escape(word) for word in BANNED_WORDS) + r")\b"
    return re.search(banned_pattern, text, re.IGNORECASE) is None
