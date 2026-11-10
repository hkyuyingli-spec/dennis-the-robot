from __future__ import annotations

from functools import lru_cache
import os
import re
from pathlib import Path
from typing import Callable

from nutribot.agents import AgentOrchestrator
from nutribot.classics import find_passages, get_disclaimer
from nutribot.rag import (
    cancer_personal_redirect_response,
    find_relevant_cancer_education,
    find_relevant_constitutions,
    find_relevant_herbs_formulas,
    format_constitution_record,
    format_herb_record,
    find_acupressure,
    find_seasonal_foods,
    find_tcm_theory,
    is_personal_symptom_query,
    load_cancer_education,
    load_acupressure,
    load_seasonal_foods,
    load_tcm_theory,
    load_tcm_constitutions,
    load_tcm_herbs_formulas,
)
from nutribot.safety import medication_dosing_redirect, sexual_wellness_safety_redirect


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@lru_cache(maxsize=1)
def _load_knowledge() -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict], list[dict]]:
    data_dir = PROJECT_ROOT / "data"
    return (
        load_tcm_constitutions(data_dir),
        load_tcm_herbs_formulas(data_dir),
        load_cancer_education(data_dir),
        load_tcm_theory(data_dir),
        load_seasonal_foods(data_dir),
        load_acupressure(data_dir),
    )


def _retrieved_knowledge(prompt: str, language: str) -> str:
    constitutions, herbs, cancer, theory, seasonal_foods, acupressure = _load_knowledge()
    matched_constitutions = find_relevant_constitutions(
        prompt, constitutions, max_matches=1, current_lang=language
    )
    matched_herbs = find_relevant_herbs_formulas(
        prompt,
        herbs,
        matched_constitutions=matched_constitutions,
        max_matches=2,
        current_lang=language,
    )
    matched_cancer = find_relevant_cancer_education(
        prompt, cancer, max_matches=1, current_lang=language
    )
    matched_theory = find_tcm_theory(prompt, theory, max_matches=1)
    matched_seasons = find_seasonal_foods(prompt, seasonal_foods, max_matches=4)
    matched_points = find_acupressure(prompt, acupressure, max_matches=3)

    snippets = [
        format_constitution_record(item)[:500] for item in matched_constitutions
    ]
    snippets.extend(
        (
            f"{format_herb_record(item)}\n"
            f"Pregnancy safety status: {item.get('pregnancy_safe', 'consult_practitioner')}.\n"
            f"Pediatric note: {item.get('pediatric_note', 'Not assessed; consult a licensed practitioner.')}\n"
            f"Review status: {item.get('review_status', 'needs_expert_review')}."
        )[:1000]
        for item in matched_herbs
    )
    if matched_cancer and len(snippets) < 3:
        item = matched_cancer[0]
        facts = "\n".join(f"- {fact}" for fact in item.get("key_facts", []))
        cancer_reference = (
            "=== PUBLIC-HEALTH CANCER EDUCATION REFERENCE ===\n"
            f"Topic: {item.get('topic_name', '')}\n"
            f"Overview: {item.get('general_overview', '')}\n"
            f"Key facts:\n{facts}\n"
            f"Source note: {item.get('source_note', '')}\n"
            "=== END OF CANCER EDUCATION REFERENCE ==="
        )
        snippets.append(cancer_reference[:1200])

    if matched_theory:
        theory_lines = ["=== REFERENCE: TCM THEORY (EDUCATIONAL; NEEDS EXPERT REVIEW) ==="]
        for framework in matched_theory:
            theory_lines.append(
                f"{framework.get('name_en', '')} ({framework.get('name_zh', '')}): "
                f"{framework.get('description', '')}"
            )
            theory_lines.extend(
                f"- {item.get('name_en', '')} ({item.get('name_zh', '')}): "
                f"{item.get('description', '')}"
                for item in framework.get("categories", [])
            )
        snippets.append("\n".join(theory_lines))

    if matched_seasons:
        season_lines = ["=== REFERENCE: SEASONAL FOODS (GENERAL EDUCATION; NEEDS EXPERT REVIEW) ==="]
        for item in matched_seasons:
            season_lines.append(
                f"{item.get('season', '')} ({item.get('season_zh', '')}); "
                f"traditional organ association: {', '.join(item.get('organs', []))}; "
                f"flavor association: {item.get('flavor', '')}."
            )
            season_lines.append(
                f"Foods to favor: {', '.join(item.get('foods_to_favor', []))}."
            )
            season_lines.append(
                f"Foods to limit: {', '.join(item.get('foods_to_limit', []))}."
            )
            season_lines.append(f"Lifestyle: {item.get('lifestyle_advice', '')}")
            season_lines.append(f"Source/review note: {item.get('source_note', '')}")
        snippets.append("\n".join(season_lines))

    if matched_points:
        point_lines = ["=== REFERENCE: ACUPRESSURE (TRADITIONAL; NEEDS EXPERT REVIEW) ==="]
        for point in matched_points:
            point_lines.extend((
                f"{point.get('code', '')} {point.get('name_en', '')} "
                f"({point.get('name_zh', '')}); pregnancy_safe="
                f"{point.get('pregnancy_safe', 'consult_practitioner')}.",
                f"Approximate location: {point.get('location', '')}",
                f"Traditional use: {point.get('traditional_use', '')}",
                f"Cautions: {point.get('cautions', '')}",
                f"Source/review note: {point.get('source_note', '')}",
            ))
        snippets.append("\n".join(point_lines))

    return "\n\n".join(snippets)[:6000]


_PREGNANCY_CONTEXT = re.compile(
    r"\b(?:pregnan\w*|expecting|hamil|kehamilan)\b|怀孕|妊娠|孕期|孕妇",
    re.IGNORECASE,
)
_PREGNANCY_REMEDY_REQUEST = re.compile(
    r"\b(?:herb\w*|herbal|formula\w*|supplement\w*|vitamin\w*|acupressure|acupuncture|"
    r"pressure point\w*)\b|草药|中药|方剂|补充剂|穴位|按压",
    re.IGNORECASE,
)


def _pregnancy_remedy_redirect(prompt: str, language: str) -> str | None:
    if not _PREGNANCY_CONTEXT.search(prompt):
        return None
    _constitutions, herbs, _cancer, _theory, _seasons, points = _load_knowledge()
    matched_herbs = find_relevant_herbs_formulas(
        prompt, herbs, matched_constitutions=[], max_matches=20, current_lang=language
    )
    matched_points = find_acupressure(prompt, points, max_matches=20)
    requests_remedy = bool(_PREGNANCY_REMEDY_REQUEST.search(prompt))
    has_unassessed_herb = any(
        item.get("pregnancy_safe") is not True for item in matched_herbs
    )
    has_restricted_point = any(
        item.get("pregnancy_safe") is not True for item in matched_points
    )
    if not (requests_remedy or has_unassessed_herb or has_restricted_point):
        return None
    responses = {
        "en": (
            "I can’t recommend or guide the use of herbs, formulas, supplements, or acupressure "
            "during pregnancy. Please consult your obstetric clinician and a licensed practitioner."
        ),
        "id": (
            "Saya tidak dapat merekomendasikan atau memandu penggunaan herbal, formula, suplemen, "
            "atau akupresur selama kehamilan. Konsultasikan dengan dokter kandungan dan praktisi berlisensi."
        ),
        "zh": (
            "妊娠期间我不能推荐或指导使用草药、方剂、补充剂或穴位按压。"
            "请咨询产科医生和持证执业人员。"
        ),
    }
    return responses.get(language, responses["en"])


def answer_chat(
    messages: list[dict],
    language: str,
    get_client: Callable,
    wrap_client: Callable,
) -> dict:
    prompt = messages[-1]["content"].strip()

    redirect = sexual_wellness_safety_redirect(prompt, language)
    if redirect:
        return {"reply": redirect, "classical_reference_used": False}

    redirect = medication_dosing_redirect(prompt, language)
    if redirect:
        return {"reply": redirect, "classical_reference_used": False}

    redirect = _pregnancy_remedy_redirect(prompt, language)
    if redirect:
        return {"reply": redirect, "classical_reference_used": False}

    if is_personal_symptom_query(prompt):
        return {
            "reply": cancer_personal_redirect_response(prompt),
            "classical_reference_used": False,
        }

    classical_passages = find_passages(prompt, max_matches=2)
    classical_reference = [
        f"[{passage['id']} | {passage['theme']}]\n"
        f"ZH: {passage['text_zh']}\n"
        f"EN: {passage['text_en']}"
        for passage in classical_passages
    ]
    context = {
        "language": language,
        "chat_history": messages[:-1][-10:],
        "retrieved_knowledge": _retrieved_knowledge(prompt, language),
    }
    if classical_reference:
        context["classical_reference"] = classical_reference
        context["classical_disclaimer"] = get_disclaimer()

    client = wrap_client(get_client(), language)
    reply = AgentOrchestrator(
        client, model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    ).respond(prompt, context=context)
    return {
        "reply": reply,
        "classical_reference_used": bool(classical_reference),
    }
