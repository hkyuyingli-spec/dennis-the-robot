import os
import json

STOP_WORDS = {
    "easily", "look", "looks", "feeling", "feel", "feels", "with", "from", "have", "has",
    "make", "body", "type", "tendency", "prone", "often", "very", "also", "some", "like",
    "soft", "good", "main", "well", "more", "less", "much", "many", "over", "under", "into"
}


def load_tcm_constitutions(data_dir=None):
    if data_dir is None:
        data_dir = os.path.join(os.getcwd(), "data")
    json_path = os.path.join(data_dir, "tcm_constitutions.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except Exception:
            pass
    return []


def find_relevant_constitutions(prompt, constitutions_data, max_matches=2):
    if not prompt or not constitutions_data:
        return []
    prompt_lower = prompt.lower()
    scored_results = []
    for item in constitutions_data:
        score = 0
        cid = item.get("id", "")
        names = [
            item.get("name_english", "").lower(),
            item.get("name_chinese", "").lower(),
            item.get("pinyin", "").lower(),
            cid.lower()
        ]
        for n in names:
            if n and n in prompt_lower:
                score += 6

        diagnostic_keywords = {
            "pinghe": ["pinghe", "平和", "balanced constitution", "harmonious constitution", "healthy constitution"],
            "qixu": ["qixu", "气虚", "qi deficiency", "qi-deficiency", "short of breath", "shortness of breath", "spontaneous sweating", "catch cold", "catching cold", "fatigue", "tired", "weak voice"],
            "yangxu": ["yangxu", "阳虚", "yang deficiency", "yang-deficiency", "cold hands", "cold feet", "cold limbs", "intolerance to cold", "cold intolerance", "warm drinks", "chilly"],
            "yinxu": ["yinxu", "阴虚", "yin deficiency", "yin-deficiency", "five-center heat", "five center heat", "night sweat", "night sweating", "sweat at night", "dry mouth", "dry throat", "chapped lips", "dry eyes"],
            "tan-shi": ["tan-shi", "tanshi", "痰湿", "phlegm-dampness", "phlegm dampness", "abdominal obesity", "greasy tongue", "heavy body", "heavy feeling", "sticky taste", "bloated", "bloating"],
            "shi-re": ["shi-re", "shire", "湿热", "damp-heat", "damp heat", "acne", "breakout", "breakouts", "bitter taste", "bitter mouth", "sticky stool", "yellow tongue"],
            "xue-yu": ["xue-yu", "xueyu", "血瘀", "blood-stasis", "blood stasis", "bruise", "bruising", "dark purple", "purple lips", "stasis spots", "hyperpigmentation"],
            "qi-yu": ["qi-yu", "qiyu", "气郁", "qi-stagnation", "qi stagnation", "frequent sighing", "sighing", "chest distension", "globus hystericus", "plum-pit", "moody", "anxious", "anxiety", "melancholy", "mood swings"],
            "te-bing": ["te-bing", "tebing", "特禀", "allergic constitution", "special constitution", "allergy", "allergies", "seasonal allergies", "allergic rhinitis", "hives", "rash", "rashes", "skin rash", "skin rashes", "asthma"]
        }

        if cid in diagnostic_keywords:
            for kw in diagnostic_keywords[cid]:
                if kw in prompt_lower:
                    score += 4

        all_phrases = item.get("key_characteristics", []) + item.get("susceptibility_conditions", [])
        for phrase in all_phrases:
            phrase_clean = phrase.lower()
            if len(phrase_clean) > 8 and phrase_clean in prompt_lower:
                score += 5

        for trait in item.get("key_characteristics", []):
            words = [w.strip(",.()") for w in trait.lower().split()]
            for w in words:
                if len(w) >= 4 and w not in STOP_WORDS and w in prompt_lower:
                    score += 1

        if score >= 4:
            scored_results.append((score, item))

    scored_results.sort(key=lambda x: x[0], reverse=True)
    return [item for score, item in scored_results[:max_matches]]


def load_tcm_herbs_formulas(data_dir=None):
    if data_dir is None:
        data_dir = os.path.join(os.getcwd(), "data")
    json_path = os.path.join(data_dir, "tcm_herbs_formulas.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                entries = data.get("entries", [])
                return entries
        except Exception:
            pass
    return []


def find_relevant_herbs_formulas(prompt, herbs_data, matched_constitutions=None, max_matches=3):
    if not prompt or not herbs_data:
        return []
    prompt_lower = prompt.lower()
    matched_constitution_ids = set(m.get("id") for m in matched_constitutions) if matched_constitutions else set()
    scored_results = []
    for item in herbs_data:
        score = 0
        hid = item.get("id", "")
        names = [
            item.get("name_english", "").lower(),
            item.get("name_chinese", "").lower(),
            item.get("pinyin", "").lower(),
            hid.lower()
        ]
        for n in names:
            if n and n in prompt_lower:
                score += 6

        herb_keywords = {
            "astragalus": ["astragalus", "huangqi", "黄芪"],
            "ginseng": ["ginseng", "renshen", "人参"],
            "goji_berry": ["goji", "wolfberry", "gouqi", "gouqizi", "枸杞"],
            "chrysanthemum": ["chrysanthemum", "juhua", "菊花"],
            "ginger": ["ginger", "shengjiang", "生姜", "ganjiang", "干姜"],
            "cinnamon": ["cinnamon", "guizhi", "rougui", "桂枝", "肉桂"],
            "licorice_root": ["licorice", "gancao", "甘草"],
            "angelica_sinensis": ["angelica", "dong quai", "danggui", "当归"],
            "poria": ["poria", "tuckahoe", "fuling", "茯苓"],
            "chenpi": ["chenpi", "tangerine peel", "mandarin peel", "陈皮"],
            "lily_bulb": ["lily bulb", "baihe", "百合"],
            "tremella": ["tremella", "snow fungus", "white jelly mushroom", "yiner", "银耳"],
            "jujube": ["jujube", "red date", "dazao", "大枣"],
            "hawthorn_berry": ["hawthorn", "shanzha", "山楂"],
            "mung_bean": ["mung bean", "lvdou", "绿豆"],
            "sijunzi_tang": ["sijunzi", "four gentlemen", "四君子汤"],
            "liuwei_dihuang_wan": ["liuwei", "rehmannia pill", "six-ingredient", "六味地黄丸"],
            "xiao_yao_san": ["xiaoyao", "free and easy wanderer", "逍遥散"],
            "yu_ping_feng_san": ["yupingfeng", "jade windscreen", "玉屏风散"],
            "erchen_tang": ["erchen", "two-cured decoction", "二陈汤"]
        }

        if hid in herb_keywords:
            for kw in herb_keywords[hid]:
                if kw in prompt_lower:
                    score += 4

        related_cons = item.get("related_constitutions", [])
        if any(cid in matched_constitution_ids for cid in related_cons):
            score += 3

        uses_text = item.get("traditional_uses", "").lower()
        for word in prompt_lower.split():
            clean_w = word.strip(",.()!?")
            if len(clean_w) >= 4 and clean_w not in STOP_WORDS and clean_w in uses_text:
                score += 1

        if score >= 4:
            scored_results.append((score, item))

    scored_results.sort(key=lambda x: x[0], reverse=True)
    return [item for score, item in scored_results[:max_matches]]


def build_rag_context(matched_constitutions, matched_herbs):
    if not matched_constitutions and not matched_herbs:
        return ""
    context_blocks = []
    if matched_constitutions:
        context_blocks.append("=== REFERENCE: BODY CONSTITUTIONS ===")
        context_blocks.append("The following verified reference data from the TCM Nine Constitution Knowledge Base matched the query:\n")
        for item in matched_constitutions:
            char_str = "\n".join("- " + c for c in item.get("key_characteristics", []))
            susc_str = "\n".join("- " + s for s in item.get("susceptibility_conditions", []))
            beneficial_str = ", ".join(item.get("dietary_recommendations", {}).get("beneficial", []))
            avoid_str = ", ".join(item.get("dietary_recommendations", {}).get("avoid", []))
            life_str = "\n".join("- " + r for r in item.get("lifestyle_rituals", []))
            herb_str = ", ".join(item.get("herbal_teas_formulas", []))
            block = (
                f"--- Constitution Type: {item['name_english']} ({item['name_chinese']} / {item['pinyin']}) ---\n"
                f"Key Characteristics:\n{char_str}\n\n"
                f"Associated Health Susceptibilities:\n{susc_str}\n\n"
                f"Dietary Recommendations:\n- Beneficial Foods: {beneficial_str}\n- Foods to Avoid: {avoid_str}\n\n"
                f"Lifestyle Rituals:\n{life_str}\n\n"
                f"Recommended Classic Formulas & Herbal Teas: {herb_str}\n"
            )
            context_blocks.append(block)
        context_blocks.append("=== END OF BODY CONSTITUTION REFERENCE DATA ===\n")
    if matched_herbs:
        context_blocks.append("=== REFERENCE: HERBS & FORMULAS ===")
        context_blocks.append("The following verified reference data from the TCM Herbs & Formulas Knowledge Base matched the query:\n")
        for item in matched_herbs:
            cat_str = "Single Herb" if item.get("category") == "single_herb" else "Classic Formula"
            block = (
                f"--- {cat_str}: {item['name_english']} ({item['name_chinese']} / {item['pinyin']}) ---\n"
                f"Category: {cat_str}\n"
                f"Traditional Uses: {item.get('traditional_uses', '')}\n"
                f"Typical Preparation: {item.get('typical_preparation', '')}\n"
                f"⚠️ Cautions & Contraindications: {item.get('cautions_and_contraindications', '')}\n"
                f"Source Note: {item.get('source_note', '')}\n"
            )
            context_blocks.append(block)
        context_blocks.append("=== END OF HERBS & FORMULAS REFERENCE DATA ===")
    return "\n".join(context_blocks)
