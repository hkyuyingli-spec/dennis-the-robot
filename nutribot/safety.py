import re
from typing import Tuple, Dict, Any, Optional

from .dce_mcc import safety_gate


SYSTEM_PROMPT_VERSION = "adult-wellness-v4"
ADULT_WELLNESS_POLICY = (
    "Answer lawful adult health and sexual-wellness questions in an educational, neutral, "
    "non-judgmental manner. Answer the question directly in your first sentence; do not lead "
    "with a disclaimer or refusal. Do not automatically refuse merely because a request includes "
    "sexual health, ageing, herbs, vitamins, supplements, or performance. Provide appropriate "
    "medical-safety caveats, avoid diagnosis and prescriptions, and encourage professional care "
    "when warranted. Do not provide explicit sexual content intended for arousal or sexual content "
    "involving minors or age-ambiguous people. Do not give medication dosing or instructions to "
    "start or stop prescribed treatment; refer medication-dosing questions to a licensed clinician. "
    "Do not assist illegal activity, self-harm, or medical emergencies; direct people in immediate "
    "danger to appropriate urgent help. "
    "For supplements, explain uncertainty and interactions; avoid specific product or dose "
    "recommendations when contraindications or medicines are mentioned. For general questions "
    "about non-prescription herb or supplement dosage, do not blanket-refuse: answer with typical "
    "adult ranges only when you can do so accurately for a named herb and "
    "specific preparation; state evidence quality, formulation variability, label guidance, and "
    "relevant interactions. Never invent a dose or imply that one dose applies to all herbs. If "
    "the herb is unspecified, explain briefly that there is no universal herbal dose and ask which "
    "herb or product the user means. For broad herb or supplement type questions, give useful "
    "examples such as culinary herbs (ginger or turmeric), traditional botanicals (ginseng or "
    "astragalus), and standardized extracts; summarize common uses and concise cautions before "
    "asking what the user wants to learn more about. Do not answer only with a request for "
    "clarification when broad educational information is possible. Do not substitute generic "
    "disclaimer paragraphs "
    "for an answer. Refuse or redirect only the unsafe part of a request, including prescription-drug "
    "dosing, minors or age-unclear sexual content, explicit erotic content, dangerous interactions, "
    "emergencies, and self-harm."
)

_GENERIC_REFUSAL = re.compile(
    r"^(?:(?:i(?:'m| am) sorry[, ]*)?(?:but\s*)?)?"
    r"i\s+(?:cannot|can not|can't|cant|am unable to)\s+"
    r"(?:provide\s+(?:that|this)(?:\s+request)?|"
    r"provide\s+dosage\s+recommendations|"
    r"help with\s+(?:that|this)(?:\s+request)?|"
    r"assist with\s+(?:that|this)(?:\s+request)?)[.! ]*$",
    re.IGNORECASE,
)
_SEXUAL_WELLNESS = re.compile(
    r"\b(?:sex(?:ual)?|erectile|libido|intimacy|sexual performance)\b", re.IGNORECASE
)
_CLEARLY_ADULT = re.compile(
    r"\b(?:adult|adults|older adult|older adults|senior|seniors)\b"
    r"|\bage(?:d)?\s*(?:over|above|of)\s*(?:18|[2-9]\d|1\d\d)\b"
    r"|\b(?:over|above)\s*(?:18|[2-9]\d|1\d\d)\b"
    r"|\b(?:18|[2-9]\d|1\d\d)\s*(?:\+|and older|or older|years? old|yo)\b",
    re.IGNORECASE,
)
_MINOR_OR_AMBIGUOUS = re.compile(
    r"\b(?:minor|underage|teen(?:s|ager|agers)?|adolescent|child(?:ren)?|kid(?:s)?|"
    r"boy|girl|under[- ]?18)\b"
    r"|\b(?:age\s*)?(?:1[0-7])\s*(?:years?\s*old|year[- ]old|yo)\b"
    r"|\bage\s*(?:of\s*)?1[0-7]\b",
    re.IGNORECASE,
)
_EXPLICIT_AROUSAL = re.compile(
    r"\b(?:porn(?:ography)?|erotic|fetish|make me horny|turn me on|"
    r"write (?:an? )?(?:explicit )?(?:erotic|sex) scene|"
    r"explicit sexual (?:story|scene|content)|graphic sexual detail)\b",
    re.IGNORECASE,
)
_MEDICATION = re.compile(
    r"\b(?:prescription|prescribed)\s+(?:medication|medicine|drug|pill|tablet)\b"
    r"|\b(?:my|current)\s+(?:prescription\s+)?medication\b"
    r"|\b(?:sildenafil|viagra|tadalafil|cialis|metformin|insulin|warfarin|"
    r"apixaban|rivaroxaban|antidepressant|blood pressure medicine)\b",
    re.IGNORECASE,
)
_MEDICATION_DOSE = re.compile(
    r"\b(?:dose|dosage|dosing|mg|milligrams?|how much|how many|"
    r"increase|decrease|double|halve)\b"
    r"|\b(?:take|use)\s+\d+\b",
    re.IGNORECASE,
)
_SUPPLEMENT_REQUEST = re.compile(
    r"\b(?:vitamin|vitamins|supplement|supplements|herb|herbs|herbal)\b",
    re.IGNORECASE,
)
_EXERCISE_REQUEST = re.compile(
    r"\b(?:exercise|exercises|workout|workouts|physical activity|fitness)\b",
    re.IGNORECASE,
)
_DOSAGE_REQUEST = re.compile(
    r"\b(?:dose|dosage|dosing|how much|how many|amount|quantity)\b",
    re.IGNORECASE,
)


def is_generic_provider_refusal(response_text: str) -> bool:
    """Recognize only short, content-free refusal text, not specific safety explanations."""
    text = (response_text or "").strip().replace("’", "'")
    return len(text.split()) <= 20 and bool(_GENERIC_REFUSAL.fullmatch(text))


def medication_dosing_redirect(prompt: str, lang: str = "en") -> Optional[str]:
    """Redirect prescription-medication dose changes to a licensed clinician."""
    text = prompt or ""
    if not (_MEDICATION.search(text) and _MEDICATION_DOSE.search(text)):
        return None
    messages = {
        "en": (
            "I can’t recommend a prescription-medication dose or dose change. The safe dose "
            "depends on your health history and other medicines. Please ask your prescriber or "
            "pharmacist before taking or changing it; seek urgent care for severe or sudden symptoms. "
            "This is general education, not medical advice."
        ),
        "id": (
            "Saya tidak dapat menyarankan dosis atau perubahan dosis obat resep. Dosis yang aman "
            "bergantung pada riwayat kesehatan dan obat lain yang digunakan. Tanyakan kepada dokter "
            "atau apoteker sebelum menggunakan atau mengubah dosis; cari pertolongan segera untuk "
            "gejala berat atau mendadak. Ini informasi edukasi umum, bukan nasihat medis."
        ),
        "zh": (
            "我不能建议处方药的剂量或剂量调整。安全剂量取决于您的健康状况和其他用药。"
            "请在服用或调整前咨询开药医生或药剂师；如出现严重或突然的症状，请及时就医。"
            "以上仅供一般教育参考，不构成医疗建议。"
        ),
    }
    return messages.get(lang, messages["en"])


def sexual_wellness_safety_redirect(prompt: str, lang: str = "en") -> Optional[str]:
    """Decline explicit arousal content and sexual guidance for minors/unclear age."""
    text = prompt or ""
    if not _SEXUAL_WELLNESS.search(text):
        return None
    if _EXPLICIT_AROUSAL.search(text):
        reason = "explicit"
    elif _MINOR_OR_AMBIGUOUS.search(text) or not _CLEARLY_ADULT.search(text):
        reason = "age"
    else:
        return None

    messages = {
        "en": {
            "explicit": (
                "I can’t help create explicit sexual content intended to arouse. I can help with "
                "neutral, educational information about adult sexual health."
            ),
            "age": (
                "I can’t provide sexual-performance guidance when the person’s age is under 18 or "
                "unclear. If this is a health concern, please speak with a licensed clinician; a "
                "minor can also talk with a trusted adult."
            ),
        },
        "id": {
            "explicit": (
                "Saya tidak dapat membuat konten seksual eksplisit yang bertujuan membangkitkan gairah. "
                "Saya dapat membantu dengan informasi edukasi yang netral tentang kesehatan seksual orang dewasa."
            ),
            "age": (
                "Saya tidak dapat memberikan panduan performa seksual jika usia orang tersebut di bawah "
                "18 tahun atau tidak jelas. Untuk masalah kesehatan, bicarakan dengan tenaga kesehatan "
                "berlisensi; anak di bawah umur juga dapat berbicara dengan orang dewasa tepercaya."
            ),
        },
        "zh": {
            "explicit": (
                "我不能创作旨在引发性兴奋的露骨性内容，但可以提供关于成年人性健康的中立教育信息。"
            ),
            "age": (
                "当对象未满 18 岁或年龄不明确时，我不能提供性表现指导。如涉及健康问题，请咨询"
                "持牌医疗专业人员；未成年人也可以向可信任的成年人求助。"
            ),
        },
    }
    language_messages = messages.get(lang, messages["en"])
    return language_messages[reason]


def safe_educational_refusal_fallback(
    prompt: str,
    provider_response: str,
    lang: str = "en",
) -> Optional[str]:
    """Provide fallback education outside herb/supplement prompts."""
    text = prompt or ""
    if not is_generic_provider_refusal(provider_response):
        return None
    if safety_gate(text).triggered or medication_dosing_redirect(text, lang):
        return None
    if _MINOR_OR_AMBIGUOUS.search(text) or _EXPLICIT_AROUSAL.search(text):
        return None
    if _SUPPLEMENT_REQUEST.search(text):
        return None

    sexual_wellness = bool(_SEXUAL_WELLNESS.search(text))
    if sexual_wellness and not _CLEARLY_ADULT.search(text):
        return None
    if not (sexual_wellness or _EXERCISE_REQUEST.search(text)):
        return None

    responses = {
        "en": (
            "Sexual wellness can change with age, and persistent changes are worth discussing with a "
            "licensed clinician. Reduced erections or sexual performance can sometimes be associated "
            "with cardiovascular disease, diabetes, medication effects, hormonal changes, stress, or "
            "mental health; this information cannot identify a cause.\n\n"
            "For lifestyle support, build activity gradually with regular walking or other aerobic "
            "exercise and strength work suited to your abilities; prioritize sleep, avoid smoking, "
            "and limit alcohol. Stop exercise and seek urgent care for chest pain or shortness of breath.\n\n"
            "Evidence for herbs and supplements marketed for sexual performance is limited and product "
            "quality varies. They can interact with prescription medicines or affect blood pressure, "
            "bleeding, or heart rhythm. There is no supplement that is appropriate for everyone; avoid "
            "unverified blends and ask a clinician or pharmacist before starting one, especially if you "
            "take medicines or have a chronic condition. Do not change prescribed treatment based on "
            "this information.\n\n"
            "For persistent symptoms, consult a licensed clinician. This is educational information, "
            "not a diagnosis or medical advice."
        ),
        "id": (
            "Kesehatan seksual dapat berubah seiring bertambahnya usia; perubahan yang menetap sebaiknya "
            "dibicarakan dengan tenaga kesehatan berlisensi. Penurunan ereksi atau performa seksual "
            "kadang berkaitan dengan penyakit kardiovaskular, diabetes, efek obat, perubahan hormon, "
            "stres, atau kesehatan mental; informasi ini tidak dapat menentukan penyebabnya.\n\n"
            "Untuk mendukung gaya hidup, tingkatkan aktivitas secara bertahap melalui jalan kaki atau "
            "aktivitas aerobik dan latihan kekuatan yang sesuai kemampuan. Prioritaskan tidur, hindari "
            "merokok, dan batasi alkohol. Hentikan aktivitas dan cari pertolongan segera bila mengalami "
            "nyeri dada atau sesak napas.\n\n"
            "Bukti manfaat herbal dan suplemen untuk performa seksual masih terbatas dan mutu produk "
            "bervariasi. Produk tersebut dapat berinteraksi dengan obat resep atau memengaruhi tekanan "
            "darah, perdarahan, atau irama jantung. Tidak ada suplemen yang cocok untuk semua orang; "
            "hindari campuran yang tidak terverifikasi dan tanyakan kepada dokter atau apoteker sebelum "
            "memulai, terutama jika menggunakan obat atau memiliki kondisi kronis. Jangan mengubah "
            "pengobatan resep berdasarkan informasi ini.\n\n"
            "Untuk gejala yang menetap, konsultasikan dengan tenaga kesehatan berlisensi. Ini informasi "
            "edukasi, bukan diagnosis atau nasihat medis."
        ),
        "zh": (
            "性健康可能随年龄变化；如果变化持续存在，建议咨询持牌医疗专业人员。勃起或性表现下降"
            "有时可能与心血管疾病、"
            "糖尿病、药物影响、激素变化、压力或心理健康有关；这些信息不能确定具体原因。\n\n"
            "生活方式方面，可根据自身能力逐步增加步行等有氧活动和力量练习，保证睡眠，避免吸烟并"
            "限制饮酒。如运动或性生活时出现胸痛或呼吸困难，请停止活动并及时寻求紧急医疗帮助。\n\n"
            "用于性表现的草药和补充剂证据有限，产品质量也不一；它们可能与处方药相互作用，或影响"
            "血压、出血风险和心律。没有适合所有人的补充剂；避免成分不明的混合产品。尤其正在服药"
            "或患有慢性病时，开始使用前请咨询医生或药剂师。不要根据这些信息更改处方治疗。\n\n"
            "症状持续时请咨询持牌医疗专业人员。以上仅供健康教育参考，不构成诊断或医疗建议。"
        ),
    }

    if sexual_wellness:
        return responses.get(lang, responses["en"])
    if _SUPPLEMENT_REQUEST.search(text):
        if _DOSAGE_REQUEST.search(text):
            dosage_responses = {
                "en": (
                    "There is no single standard dose for an unspecified herb or supplement. "
                    "Dosage depends on the exact plant, preparation or extract, product strength, "
                    "and available evidence. Check the label and use a quality-tested product; "
                    "avoid combining products or exceeding label directions. Evidence varies, and "
                    "products can interact with medicines or be unsuitable for some conditions. "
                    "Ask a clinician or pharmacist before use if you take medicines, are pregnant "
                    "or breastfeeding, or have a health condition. Share the product name if you "
                    "would like general information about its evidence and cautions."
                ),
                "id": (
                    "Tidak ada satu dosis baku untuk herbal atau suplemen yang tidak disebutkan "
                    "secara spesifik. Dosis bergantung pada tanaman, bentuk sediaan atau ekstrak, "
                    "kekuatan produk, dan bukti yang tersedia. Periksa label dan gunakan produk "
                    "berkualitas; jangan menggabungkan produk atau melebihi petunjuk label. Bukti "
                    "bervariasi dan produk dapat berinteraksi dengan obat atau tidak sesuai untuk "
                    "kondisi tertentu. Tanyakan kepada tenaga kesehatan atau apoteker jika Anda "
                    "menggunakan obat, sedang hamil atau menyusui, atau memiliki kondisi kesehatan."
                ),
                "zh": (
                    "未具体说明的草药或补充剂没有统一的标准剂量。用量取决于具体植物、制剂或提取物、"
                    "产品浓度及现有证据。请查看标签并选择经过质量检测的产品；不要混用多种产品或"
                    "超过标签说明。相关证据各异，产品也可能与药物相互作用或不适合某些健康状况。"
                    "如正在用药、怀孕或哺乳，或有健康问题，请先咨询医生或药剂师。"
                ),
            }
            return dosage_responses.get(lang, dosage_responses["en"])
        exercise_responses = {
            "en": (
                "Vitamin and supplement benefits depend on diet, health history, and sometimes lab results; "
                "they do not replace a varied diet or clinical care. Evidence and product quality vary, "
                "and supplements can interact with medicines or be unsuitable for some conditions. Avoid "
                "high-dose or multi-product combinations, and check with a clinician or pharmacist before "
                "starting a supplement if you take prescription medicines or have a chronic condition. "
                "This is educational information, not a diagnosis or medical advice."
            ),
            "id": (
                "Manfaat vitamin dan suplemen bergantung pada pola makan, riwayat kesehatan, dan terkadang "
                "hasil pemeriksaan. Suplemen tidak menggantikan pola makan beragam atau perawatan klinis. "
                "Bukti dan mutu produk bervariasi; suplemen dapat berinteraksi dengan obat atau tidak cocok "
                "untuk kondisi tertentu. Hindari dosis tinggi atau kombinasi banyak produk. Jika menggunakan "
                "obat resep atau memiliki kondisi kronis, tanyakan kepada dokter atau apoteker sebelum "
                "memulai suplemen. Ini informasi edukasi, bukan diagnosis atau nasihat medis."
            ),
            "zh": (
                "维生素和补充剂的益处取决于饮食、健康状况，有时也取决于化验结果；它们不能替代多样化"
                "饮食或临床护理。相关证据"
                "和产品质量不一，补充剂可能与药物相互作用，也可能不适合某些健康状况。避免大剂量"
                "或同时使用多种产品；若正在服用处方药或患有慢性病，请在开始前咨询医生或药剂师。"
                "以上仅供健康教育参考，不构成诊断或医疗建议。"
            ),
        }
        return exercise_responses.get(lang, exercise_responses["en"])
    return {
        "en": (
            "Regular physical activity can support overall health. Start gradually with activity that "
            "matches your current ability, and consider a mix of aerobic movement and strength exercises. "
            "If you have a chronic condition, have been inactive, or develop pain, dizziness, chest pain, "
            "or shortness of breath, ask a clinician what level is appropriate; seek urgent care for "
            "chest pain or trouble breathing. This is educational information, not medical advice."
        ),
        "id": (
            "Aktivitas fisik teratur dapat mendukung kesehatan secara keseluruhan. Mulailah bertahap "
            "sesuai kemampuan, dengan kombinasi aktivitas aerobik dan latihan kekuatan. Jika memiliki "
            "kondisi kronis, lama tidak aktif, atau mengalami nyeri, pusing, nyeri dada, maupun sesak "
            "napas, tanyakan tingkat aktivitas yang sesuai kepada tenaga kesehatan; cari pertolongan "
            "segera untuk nyeri dada atau kesulitan bernapas. Ini informasi edukasi, bukan nasihat medis."
        ),
        "zh": (
            "规律活动有助于整体健康。请根据当前能力逐步开始，并考虑结合有氧活动和力量练习。如患有"
            "慢性疾病、长期缺乏运动，或出现"
            "疼痛、头晕、胸痛或呼吸困难，请咨询医疗专业人员以确定适合的活动量；胸痛或呼吸困难时"
            "请及时寻求紧急医疗帮助。以上仅供健康教育参考，不构成医疗建议。"
        ),
    }.get(
        lang,
        "This is educational information, not a diagnosis or medical advice.",
    )


# Explicit health conditions or medication use that can make herb/supplement advice higher risk.
CONDITION_KEYWORDS = [
    r"\bpregnan\w*", r"\bhamil\b", r"\bkehamilan\b",
    r"\bbreast.?feeding\b", r"\bmenyusui\b",
    r"\bblood thinners?\b", r"\banticoagulants?\b", r"\bwarfarin\b",
    r"\bdiabet(?:es|ic)\b", r"\bdiabetes\b",
    r"\bliver (?:disease|condition|failure)\b", r"\b(?:liver|hepatic) disease\b",
    r"\bkidney (?:disease|condition|failure)\b", r"\b(?:kidney|renal) disease\b",
    r"\bheart disease\b", r"\bheart condition\b", r"\bhigh blood pressure\b",
    r"\bprescription (?:medication|medicine|drug)\b", r"\bprescribed medication\b",
    r"\bminum obat resep\b", r"\bobat resep\b",
]


# Dosage-like patterns (numbers, fractions, plus units / frequency phrases)
DOSAGE_PATTERN = re.compile(
    r"(?:\b(?:\d+|\d+\/\d+|\d+\.\d+)(?:\s*(?:-\s*\d+|/\d+)?)\b)\s*(?:teaspoon|teaspoons|tsp|sendok|sendok\s*teh|sendok\s*makan|tablespoon|tbsp|tablespoons|gram|g|mg|ml|milliliter|ounce|oz|drop|drops)\b|(?:once daily|twice daily|per day|per hari|kali sehari|kali/hari|sehari|daily|times daily)",
    re.IGNORECASE
)


def _has_relevant_condition(text: str) -> bool:
    t = text.lower()
    return any(re.search(k, t) for k in CONDITION_KEYWORDS)


def _has_dosage(text: str) -> bool:
    return bool(DOSAGE_PATTERN.search(text))


def sanitize_response(
    response_text: str,
    lang: str = "en",
    user_prompt: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Inspect a generated response and remove any dosage recommendations when
    the user's prompt explicitly mentions a relevant health condition or medication.

    Returns a tuple of (sanitized_text, info) where info contains keys:
      - sanitized: bool
      - removed_sentences: list[str]
      - found_contra: bool
    """
    if not response_text:
        return response_text, {"sanitized": False, "removed_sentences": [], "found_contra": False}

    condition_context = user_prompt if user_prompt is not None else response_text
    found_contra = _has_relevant_condition(condition_context)
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
    kept_has_contra = _has_relevant_condition(kept_text)

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
