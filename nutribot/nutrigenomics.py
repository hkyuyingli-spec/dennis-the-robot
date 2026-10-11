"""Cautious, non-prescriptive notes for selected nutrigenomic markers."""

DISCLAIMER = (
    "Educational information only; a genetic marker alone does not establish a "
    "nutrient need or replace advice from a qualified clinician."
)

NUTRIGENOMIC_MAP = {
    "MTHFR": {
        "supplement": "No MTHFR-specific supplement recommendation; folic acid remains appropriate when indicated by standard guidance.",
        "evidence_note": (
            "Common MTHFR variants do not mean a person cannot process folic acid and do "
            "not, by themselves, establish a need for methylfolate. Follow standard folic "
            "acid guidance and discuss individual results with a clinician."
        ),
        "citation_url": "https://www.cdc.gov/folic-acid/data-research/mthfr/index.html",
    },
    "COMT": {
        "supplement": "No COMT-specific supplement recommendation.",
        "evidence_note": (
            "COMT has a role in catecholamine metabolism, but common COMT variants are not "
            "a validated standalone basis for choosing magnesium or another supplement."
        ),
        "citation_url": "https://medlineplus.gov/genetics/gene/comt/",
    },
    "APOE4": {
        "supplement": "No APOE4-specific supplement recommendation.",
        "evidence_note": (
            "APOE ε4 is a risk factor, not a diagnosis or a supplement indication. Current "
            "genetic risk information does not establish that omega-3 or another supplement "
            "prevents Alzheimer disease in APOE ε4 carriers."
        ),
        "citation_url": "https://www.nia.nih.gov/health/alzheimers-causes-and-risk-factors/what-do-we-know-about-alzheimers-disease-genetics",
    },
}


def recommend_from_markers(markers: dict) -> list[dict]:
    """Return evidence notes for recognized markers without interpreting genotypes."""
    if not isinstance(markers, dict):
        raise TypeError("markers must be a dict")

    results = []
    seen = set()
    for marker in markers:
        if not isinstance(marker, str):
            continue
        normalized_marker = marker.strip().upper()
        if normalized_marker in NUTRIGENOMIC_MAP and normalized_marker not in seen:
            entry = NUTRIGENOMIC_MAP[normalized_marker]
            results.append({
                "supplement": entry["supplement"],
                "note": entry["evidence_note"],
                "citation_url": entry["citation_url"],
                "disclaimer": DISCLAIMER,
            })
            seen.add(normalized_marker)
    return results
