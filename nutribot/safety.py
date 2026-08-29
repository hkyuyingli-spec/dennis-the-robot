import re
from typing import Tuple, Dict, Any


# Contraindication keywords (English + Indonesian + common stems)
CONTRA_KEYWORDS = [
    r"\bpregnan", r"\bpregnancy\b", r"\bhamil\b", r"\bkehamilan\b",
    r"\bcontraindicat", r"\bcontraindicated\b", r"\bavoid\b", r"\bkontraindikasi\b", r"\bhindari\b"
]


# Dosage-like patterns (numbers, fractions, plus units / frequency phrases)
DOSAGE_PATTERN = re.compile(
    r"(?:\b(?:\d+|\d+\/\d+|\d+\.\d+)(?:\s*(?:-\s*\d+|/\d+)?)\b)\s*(?:teaspoon|teaspoons|tsp|sendok|sendok\s*teh|sendok\s*makan|tablespoon|tbsp|tablespoons|gram|g|mg|ml|milliliter|ounce|oz|drop|drops)\b|(?:once daily|twice daily|per day|per hari|kali sehari|kali/hari|sehari|daily|times daily)",
    re.IGNORECASE
)


def _has_contraindication(text: str) -> bool:
    t = text.lower()
    return any(re.search(k, t) for k in CONTRA_KEYWORDS)


def _has_dosage(text: str) -> bool:
    return bool(DOSAGE_PATTERN.search(text))


def sanitize_response(response_text: str, lang: str = "en") -> Tuple[str, Dict[str, Any]]:
    """
    Inspect a generated response and remove any dosage recommendations when
    contraindication language also appears in the response.

    Returns a tuple of (sanitized_text, info) where info contains keys:
      - sanitized: bool
      - removed_sentences: list[str]
      - found_contra: bool
    """
    if not response_text:
        return response_text, {"sanitized": False, "removed_sentences": [], "found_contra": False}

    found_contra = _has_contraindication(response_text)
    found_dosage = _has_dosage(response_text)

    if not (found_contra and found_dosage):
        return response_text, {"sanitized": False, "removed_sentences": [], "found_contra": found_contra}

    # Split into sentences (simple heuristic)
    sentences = re.split(r'(?<=[\.!?。\n])\s+', response_text)
    removed = []
    kept = []
    for s in sentences:
        if DOSAGE_PATTERN.search(s):
            removed.append(s.strip())
        else:
            kept.append(s)

    # Ensure we still communicate the contraindication. If not present in kept sentences,
    # build a conservative fallback in the target language.
    kept_text = " ".join(kept).strip()
    kept_has_contra = _has_contraindication(kept_text)

    if not kept_has_contra:
        # Language-specific conservative fallback
        fallbacks = {
            "en": (
                "CRITICAL SAFETY: This herb/formula has contraindications for your condition (e.g., pregnancy). "
                "Do NOT use or self-dose. Consult a qualified practitioner or doctor before use."
            ),
            "id": (
                "KEAMANAN KRITIS: Ramuan ini memiliki kontraindikasi untuk kondisi Anda (mis. kehamilan). "
                "JANGAN digunakan atau mencoba dosis sendiri. Konsultasikan dengan praktisi yang berkualifikasi atau dokter sebelum digunakan."
            ),
            "zh": (
                "关键安全警告：该草药/方剂对您的状况（例如孕期）有禁忌。请勿自行使用或自行给药。请咨询合格的从业人员或医生。"
            )
        }
        fallback = fallbacks.get(lang, fallbacks["en"])
        sanitized = fallback
    else:
        sanitized = kept_text

    # Always ensure the educational disclaimer remains at the end if present in original
    if "⚕️ For educational purposes only." in response_text and "⚕️ For educational purposes only." not in sanitized:
        sanitized = sanitized + "\n\n⚕️ For educational purposes only. Please consult a qualified TCM practitioner for proper diagnosis and treatment."

    info = {"sanitized": True, "removed_sentences": removed, "found_contra": True}
    return sanitized, info
