#!/usr/bin/env python3
"""Validate Herbal Kitchen content using only Python's standard library."""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parent
DATA_PATH = TOOLS_DIR.parent / "src" / "data" / "herbal_kitchen.json"
REPORT_PATH = TOOLS_DIR / "last_report.txt"
VALID_STATUSES = {"draft", "verified", "published"}
BANNED_WORDS = [
    "boost", "detox", "immunity", "cleanse", "heal", "cure", "remedy",
    "therapeutic", "anti-inflammatory", "nourish", "lowers blood",
    "reduces cholesterol", "weight loss", "cooling", "heating",
    "menyembuhkan", "mengobati", "detoks", "imun", "daya tahan tubuh", "khasiat",
    "\u6cbb\u7597", "\u6cbb\u75c5", "\u6392\u6bd2", "\u517b\u751f",
    "\u589e\u5f3a\u514d\u75ab", "\u6ecb\u8865", "\u8865\u6c14", "\u8865\u8840", "\u529f\u6548",
]
DISALLOWED_HERBS = [
    "ginseng", "danshen", "dong quai", "angelica", "ginkgo", "licorice",
    "safflower", "peach kernel", "notoginseng", "star fruit",
]
ALLERGEN_PATTERNS = {
    "sesame": re.compile(r"\bsesame\b", re.I),
    "nuts": re.compile(r"\b(?:nuts?|candlenuts?)\b", re.I),
    "peanut": re.compile(r"\bpeanuts?\b", re.I),
    "shrimp": re.compile(r"\bshrimps?\b", re.I),
    "soy": re.compile(r"\bsoy\b", re.I),
    "egg": re.compile(r"\beggs?\b", re.I),
    "fish": re.compile(r"\bfish\b", re.I),
    "milk": re.compile(r"\bmilk\b", re.I),
    "wheat": re.compile(r"\bwheat\b", re.I),
}
DIET_RESTRICTIONS = {
    "vegetarian": re.compile(
        r"\b(?:meat|poultry|chicken|beef|pork|lamb|duck|turkey|fish|shrimp|"
        r"fish sauce|shrimp paste|oyster sauce|gelatin)\b", re.I
    ),
    "no-pork": re.compile(r"\b(?:pork|lard|bacon|babi)\b", re.I),
    "no-alcohol": re.compile(r"\b(?:wine|rum|beer|arak|liquor)\b", re.I),
}


def strings_in(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from strings_in(child)
    elif isinstance(value, list):
        for child in value:
            yield from strings_in(child)


def localized_objects(value):
    if isinstance(value, dict):
        if any(key in value for key in ("en", "id", "zh")):
            yield value
        for child in value.values():
            yield from localized_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from localized_objects(child)


def has_chinese(value):
    return isinstance(value, str) and re.search(r"[\u3400-\u9fff]", value) is not None


def has_phrase(text, phrase):
    if re.search(r"[a-z]", phrase, re.I):
        return re.search(r"(?<![a-z])" + re.escape(phrase) + r"(?![a-z])", text, re.I) is not None
    return phrase.casefold() in text.casefold()


def normalized_allergens(values):
    result = set()
    for value in values if isinstance(values, list) else []:
        text = str(value).casefold().replace("-", "_").replace(" ", "_")
        if "nut" in text or "candlenut" in text:
            result.add("nuts")
        for name in ALLERGEN_PATTERNS:
            if name != "nuts" and name in text:
                result.add(name)
    return result


def category_for(message, severity):
    text = message.casefold()
    if "duplicate id" in text:
        return "duplicate IDs"
    if "invalid status" in text:
        return "status values"
    if "banned claim word" in text:
        return "banned claims"
    if "disallowed herb" in text:
        return "disallowed herbs"
    if "herbid" in text or "references unknown" in text:
        return "herb references"
    if "diet" in text and "conflicts" in text:
        return "diet conflicts"
    if "candlenut" in text and "warning" in text:
        return "candlenut safety"
    if "published dish" in text:
        return "published record requirements"
    if "missing name" in text or "missing steps" in text or "missing ingredients" in text:
        return "required dish fields"
    if "missing zh text" in text:
        return "missing Chinese text"
    if "has no qty" in text:
        return "missing ingredient quantities"
    if "without listing it in allergens" in text:
        return "undeclared allergens"
    if "chicken dish" in text:
        return "chicken safety"
    return "other"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true", help="print every error and warning")
    args = parser.parse_args()
    errors = []
    warnings = []
    try:
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"could not read valid JSON: {exc}")
        data = {"herbs": [], "dishes": []}

    herbs = data.get("herbs", [])
    dishes = data.get("dishes", [])
    herb_ids = {herb.get("id") for herb in herbs if isinstance(herb, dict)}
    seen = {}
    for group, records in (("herb", herbs), ("dish", dishes)):
        for record in records:
            if not isinstance(record, dict):
                errors.append(f"{group} record is not an object")
                continue
            record_id = record.get("id")
            if record_id in seen:
                errors.append(f"duplicate id {record_id!r} ({seen[record_id]} and {group})")
            else:
                seen[record_id] = group
            if record.get("status") not in VALID_STATUSES:
                errors.append(f"{group} {record_id!r} has invalid status {record.get('status')!r}")
            record_text = "\n".join(strings_in(record))
            for word in BANNED_WORDS:
                if has_phrase(record_text, word):
                    errors.append(f"banned claim word {word!r} in {group} {record_id!r}")
            for term in DISALLOWED_HERBS:
                if has_phrase(record_text, term):
                    errors.append(f"disallowed herb {term!r} in {group} {record_id!r}")

    for dish in dishes:
        if not isinstance(dish, dict):
            continue
        dish_id = dish.get("id", "<unknown>")
        name = dish.get("name")
        if not isinstance(name, dict) or not all(
            isinstance(name.get(lang), str) and name[lang].strip() for lang in ("en", "id")
        ):
            errors.append(f"dish {dish_id!r} is missing name in en or id")
        for field in ("steps", "ingredients"):
            values = dish.get(field)
            if not isinstance(values, list) or not values:
                errors.append(f"dish {dish_id!r} is missing {field}")
                continue
            for index, item in enumerate(values):
                localized = item.get("text", {}) if field == "ingredients" and isinstance(item, dict) else item
                for lang in ("en", "id"):
                    if not isinstance(localized, dict) or not isinstance(localized.get(lang), str) or not localized[lang].strip():
                        errors.append(f"dish {dish_id!r} {field}[{index}] is missing {lang} text")
                zh_value = localized.get("zh") if isinstance(localized, dict) else None
                if not isinstance(zh_value, str) or not zh_value.strip() or "??" in zh_value or not has_chinese(zh_value):
                    warnings.append(f"dish {dish_id!r} {field}[{index}] is missing zh text")

        for localized in localized_objects({key: dish.get(key) for key in ("name", "intro", "tips", "variations", "storage")}):
            zh_value = localized.get("zh")
            if not isinstance(zh_value, str) or not zh_value.strip() or "??" in zh_value or not has_chinese(zh_value):
                warnings.append(f"dish {dish_id!r} has missing zh text")

        ingredients = dish.get("ingredients", [])
        if not isinstance(ingredients, list):
            ingredients = []
        declared = normalized_allergens(dish.get("allergens", []))
        for index, ingredient in enumerate(ingredients):
            if not isinstance(ingredient, dict):
                continue
            if ingredient.get("herbId") is not None and ingredient.get("herbId") not in herb_ids:
                errors.append(f"dish {dish_id!r} ingredient {index} references unknown herbId {ingredient.get('herbId')!r}")
            if ingredient.get("qty") is None:
                warnings.append(f"dish {dish_id!r} ingredient {index} has no qty")
            text = " ".join(strings_in(ingredient.get("text", {})))
            for allergen, pattern in ALLERGEN_PATTERNS.items():
                if pattern.search(text) and allergen not in declared:
                    warnings.append(f"dish {dish_id!r} ingredient {index} mentions {allergen} without listing it in allergens")

        all_dish_text = "\n".join(strings_in(dish))
        ingredient_text = " ".join(
            text for ingredient in ingredients if isinstance(ingredient, dict)
            for text in strings_in(ingredient.get("text", {}))
        )
        for diet in dish.get("diet", []) if isinstance(dish.get("diet"), list) else []:
            restriction = DIET_RESTRICTIONS.get(diet)
            if restriction and restriction.search(ingredient_text):
                errors.append(f"dish {dish_id!r} diet {diet!r} conflicts with its ingredients")
        if re.search(r"\bchicken\b", all_dish_text, re.I):
            steps_text = " ".join(strings_in(dish.get("steps", [])))
            if not re.search(r"cooked through|\b\d+(?:\.\d+)?\s*(?:\u00b0\s*)?(?:c|f)\b", steps_text, re.I):
                warnings.append(f"chicken dish {dish_id!r} steps lack a cooked-through phrase or temperature")
        if re.search(r"candlenut|kemiri", all_dish_text, re.I):
            safety = dish.get("cookingSafety")
            warning = "Cook or roast candlenuts before eating; do not eat them raw."
            if not isinstance(safety, dict) or any(safety.get(lang) != warning for lang in ("en", "id", "zh")):
                errors.append(f"candlenut dish {dish_id!r} is missing the required raw-candlenut warning")
        sources = dish.get("sources", [])
        if dish.get("status") == "published" and (
            not isinstance(sources, list) or len(sources) < 2 or not str(dish.get("checkedOn", "")).strip()
        ):
            errors.append(f"published dish {dish_id!r} needs at least 2 sources and a checkedOn date")

    for herb in herbs:
        if not isinstance(herb, dict):
            continue
        herb_id = herb.get("id", "<unknown>")
        for localized in localized_objects(herb):
            zh_value = localized.get("zh")
            if not isinstance(zh_value, str) or not zh_value.strip() or "??" in zh_value or not has_chinese(zh_value):
                warnings.append(f"herb {herb_id!r} is missing zh text")

    categories = {
        "ERRORS": defaultdict(list),
        "WARNINGS": defaultdict(list),
    }
    for severity, messages in (("ERRORS", errors), ("WARNINGS", warnings)):
        for message in messages:
            categories[severity][category_for(message, severity)].append(message)

    full_lines = [
        f"Herbal Kitchen validation: {len(herbs)} herbs, {len(dishes)} dishes",
        f"ERRORS ({len(errors)})",
    ]
    full_lines.extend(f"- {item}" for item in errors) if errors else full_lines.append("- None")
    full_lines.append(f"WARNINGS ({len(warnings)})")
    full_lines.extend(f"- {item}" for item in warnings) if warnings else full_lines.append("- None")
    full_report = "\n".join(full_lines) + "\n"
    try:
        REPORT_PATH.write_text(full_report, encoding="utf-8")
    except OSError as exc:
        errors.append(f"could not write full report: {exc}")

    if args.verbose:
        print(full_report, end="")
    else:
        print(f"SUMMARY: {len(errors)} errors, {len(warnings)} warnings")
        for severity in ("ERRORS", "WARNINGS"):
            print(severity)
            groups = categories[severity]
            if not groups:
                print("  none")
                continue
            for category, messages in sorted(groups.items()):
                print(f"  {category}: {len(messages)}")
                for message in messages[:5]:
                    print(f"    - {message}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
