from __future__ import annotations

from functools import lru_cache
import os
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
    is_personal_symptom_query,
    load_cancer_education,
    load_tcm_constitutions,
    load_tcm_herbs_formulas,
)
from nutribot.safety import medication_dosing_redirect, sexual_wellness_safety_redirect


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@lru_cache(maxsize=1)
def _load_knowledge() -> tuple[list[dict], list[dict], list[dict]]:
    data_dir = PROJECT_ROOT / "data"
    return (
        load_tcm_constitutions(data_dir),
        load_tcm_herbs_formulas(data_dir),
        load_cancer_education(data_dir),
    )


def _retrieved_knowledge(prompt: str, language: str) -> str:
    constitutions, herbs, cancer = _load_knowledge()
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

    snippets = [
        format_constitution_record(item)[:300] for item in matched_constitutions
    ]
    snippets.extend(format_herb_record(item)[:300] for item in matched_herbs)
    context = "\n\n".join(snippets[:3])
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
        context = "\n\n".join(part for part in (context, cancer_reference[:1200]) if part)
    return context[:3200]


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
