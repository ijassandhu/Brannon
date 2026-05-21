# -*- coding: utf-8 -*-
import math
import json
import re
import logging
import requests
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


_ELEMENT_FIELD_MAP = {
    "c": "c_element",
    "mn": "mn_element",
    "si": "si_element",
    "p": "p_element",
    "s": "s_element",
    "b": "b_element",
    "nb": "nb_element",
    "ti": "ti_element",
    "al": "al_element",
    "ca": "ca_element",
    "zr": "zr_element",
    "zn": "zn_element",
    "sn": "sn_element",
    "cu": "cu_element",
    "ni": "ni_element",
    "cr": "cr_element",
    "mo": "mo_element",
    "n": "n_element",
    "v": "v_element",
}


def _round5(value):
    if value in (None, False, ""):
        return None
    try:
        return round(float(value), 5)
    except (TypeError, ValueError):
        return None


def _safe_float(value):
    if value in (None, False, ""):
        return None
    return _round5(value)


def _normalize_text(value):
    return (value or "").strip().lower()


def _extract_json(text):
    if not text:
        return None
    if isinstance(text, dict):
        return text
    if not isinstance(text, str):
        return None
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*", "", candidate, flags=re.IGNORECASE)
        candidate = re.sub(r"\s*```$", "", candidate)
    if candidate:
        try:
            return json.loads(candidate)
        except Exception:
            pass
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(candidate[start:end + 1])
        except Exception:
            return None
    return None

def _clean_spec_name(value):
    s = (value or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s

def _normalize_heat(value):
    s = (value or "").upper()
    s = re.sub(r"[^A-Z0-9]+", "", s)
    return s.strip()


def _normalize_branch_key(value):
    text = (value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "branch_1"


def _split_equivalents(value):
    if not value:
        return []
    if isinstance(value, (list, tuple, set)):
        items = []
        for v in value:
            items.extend(_split_equivalents(v))
        return items
    text = str(value)
    # Split on common separators: comma, semicolon, pipe, newline
    parts = re.split(r"[,\n;|]+", text)
    expanded = []
    for part in parts:
        p = part.strip()
        if not p:
            continue
        # Split on slash when it looks like dual specs (e.g., A182/A350)
        if "/" in p and re.search(r"[A-Z]\d", p.upper()):
            expanded.extend([s.strip() for s in p.split("/") if s.strip()])
        else:
            expanded.append(p)
    return expanded


def _normalize_grade(value):
    text = _normalize_text(value)
    if not text:
        return ""
    # Remove common boilerplate tokens to match "ASTM A36" with "A36"
    text = re.sub(r"\b(astm|asme|api|aisi|grade)\b", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_grade_tokens(value):
    """
    Extract comparable grade tokens from mixed/compound grade strings.
    Examples:
      "CSA G40.21 50W / ASTM A572 GR 50 TY 2" -> ["g4021 50w", "a572 gr 50", "a572 50"]
      "ALGOMA 100 (96) / ASTM A514 GR S" -> ["a514 gr s", "a514 s"]
    """
    if not value:
        return []
    text = str(value)
    text = re.sub(r"\s+", " ", text).strip()

    tokens = set()

    # Match ASTM/ASME/API/AISI Axxx forms (optionally with GR/Grade)
    for m in re.finditer(r"\b(?:ASTM|ASME|API|AISI)\s*(A\d{2,4}[A-Z]?)\b", text, re.IGNORECASE):
        code = m.group(1).upper()
        suffix = ""
        after = text[m.end(): m.end() + 30]
        g = re.search(r"\b(?:GR|GRADE)\s*([A-Z0-9]+(?:\s*\d+)?)\b", after, re.IGNORECASE)
        if g:
            suffix = g.group(1).strip()
        base = code.lower()
        if suffix:
            tokens.add(f"{base} gr {suffix.lower()}")
        # also add base without grade to allow loose matching (A572)
        tokens.add(base)

    # Match CSA G40.21 50W
    for m in re.finditer(r"\bCSA\s*G\s*40\.?21\s*([0-9]{2,3}\s*[A-Z]?)\b", text, re.IGNORECASE):
        grade = m.group(1).replace(" ", "").upper()
        tokens.add(f"g4021 {grade.lower()}")

    # Match plain A###, A###X, etc if present in text
    for m in re.finditer(r"\bA\d{2,4}[A-Z]?\b", text, re.IGNORECASE):
        tokens.add(m.group(0).lower())

    # Match standalone GR/Grade tokens with context e.g., "A514 GR S"
    # If no ASTM code captured, still try to keep "gr X" as a weak token
    if not tokens:
        for m in re.finditer(r"\b(?:GR|GRADE)\s*([A-Z0-9]+)\b", text, re.IGNORECASE):
            tokens.add(f"gr {m.group(1).lower()}")

    return list(tokens)


def _parse_first_number(text):
    if not text:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not match:
        return None
    return _round5(match.group(1))


def _parse_thickness(dimensions):
    if not dimensions:
        return None
    # Try to parse typical formats like "1.5 x 96 x 240" or "1-1/2 X 96".
    text = str(dimensions).replace("×", "x").replace("X", "x")
    unit_hint = _normalize_text(text)
    parts = [p.strip() for p in text.split("x") if p.strip()]
    if parts:
        # First segment is usually thickness.
        first = parts[0]
        # Handle simple fraction like 1-1/2.
        if "-" in first and "/" in first:
            try:
                whole, frac = first.split("-", 1)
                num, den = frac.split("/", 1)
                return _round5(float(whole) + (float(num) / float(den)))
            except Exception:
                pass
        # Handle fraction like 1/2.
        if "/" in first:
            try:
                num, den = first.split("/", 1)
                value = _round5(float(num) / float(den))
                if "mm" in unit_hint:
                    return _mm_to_in(value)
                if "cm" in unit_hint:
                    return _cm_to_in(value)
                return value
            except Exception:
                pass
        value = _parse_first_number(first)
        if value is None:
            return None
        if "mm" in unit_hint:
            return _mm_to_in(value)
        if "cm" in unit_hint:
            return _cm_to_in(value)
        return value
    value = _parse_first_number(dimensions)
    if value is None:
        return None
    if "mm" in unit_hint:
        return _mm_to_in(value)
    if "cm" in unit_hint:
        return _cm_to_in(value)
    return value


def _normalize_rule_operator(value):
    op = _normalize_text(value)
    aliases = {
        "=": "=",
        "==": "=",
        "eq": "=",
        "equals": "=",
        "equal": "=",
        "!=": "!=",
        "<>": "!=",
        "ne": "!=",
        "not_equal": "!=",
        ">": ">",
        "gt": ">",
        "greater": ">",
        ">=": ">=",
        "gte": ">=",
        "ge": ">=",
        "<": "<",
        "lt": "<",
        "less": "<",
        "<=": "<=",
        "lte": "<=",
        "le": "<=",
        "contains": "contains",
        "not_contains": "not_contains",
        "startswith": "starts_with",
        "starts_with": "starts_with",
        "endswith": "ends_with",
        "ends_with": "ends_with",
        "in": "in",
        "not_in": "not_in",
        "exists": "exists",
        "missing": "missing",
    }
    return aliases.get(op, op)


def _split_rule_values(value):
    if value in (None, False, ""):
        return []
    if isinstance(value, (list, tuple, set)):
        items = []
        for item in value:
            items.extend(_split_rule_values(item))
        return [item for item in items if item not in (None, "", False)]
    text = str(value)
    parts = re.split(r"[,\n;|]+", text)
    return [part.strip() for part in parts if part and part.strip()]


def _rule_number_with_unit(value, unit, field_name):
    num = _safe_float(value)
    if num is None:
        return None
    field = _normalize_text(field_name)
    u = _normalize_text(unit)
    if field in ("yield_strength", "tensile_strength", "yield", "tensile"):
        if u in ("mpa", "megapascal", "megapascals"):
            return _mpa_to_psi(num)
        if u in ("ksi", "ks", "kpsi"):
            return _ksi_to_psi(num)
        return num
    if field in ("hardness", "hbw", "bhn", "brinell"):
        return num
    if field in ("elongation", "reduction_area", "reductionarea", "ra"):
        return num
    if field in ("thickness", "plate_dimension", "dimensions", "width", "height", "wall_thickness"):
        if u in ("mm", "millimeter", "millimeters"):
            return _mm_to_in(num)
        if u in ("cm", "centimeter", "centimeters"):
            return _cm_to_in(num)
        return num
    if field in ("impact_test_temp", "temperature", "test_temperature"):
        if u in ("c", "celsius", "deg c", "°c", "celcius"):
            return _c_to_f(num)
        return num
    return num


def _rule_subject_from_field(field_name, mtr, inventory, mtr_values):
    field = _normalize_text(field_name)
    if not field:
        return None

    derived_thickness = _parse_thickness(getattr(inventory, "dimensions", None)) if inventory else None

    mapping = {
        "c": mtr_values.get("c"),
        "mn": mtr_values.get("mn"),
        "si": mtr_values.get("si"),
        "p": mtr_values.get("p"),
        "s": mtr_values.get("s"),
        "b": mtr_values.get("b"),
        "nb": mtr_values.get("nb"),
        "ti": mtr_values.get("ti"),
        "al": mtr_values.get("al"),
        "ca": mtr_values.get("ca"),
        "zr": mtr_values.get("zr"),
        "zn": mtr_values.get("zn"),
        "sn": mtr_values.get("sn"),
        "cu": mtr_values.get("cu"),
        "ni": mtr_values.get("ni"),
        "cr": mtr_values.get("cr"),
        "mo": mtr_values.get("mo"),
        "n": mtr_values.get("n"),
        "v": mtr_values.get("v"),
        "yield_strength": _safe_float(getattr(mtr, "yield_strength", None)),
        "tensile_strength": _safe_float(getattr(mtr, "tensile_strength", None)),
        "elongation": _safe_float(getattr(mtr, "elongation", None)),
        "reduction_area": _safe_float(getattr(mtr, "reduction_area", None)),
        "hardness": _safe_float(getattr(mtr, "hardness", None)),
        "impact_test_temp": _safe_float(getattr(mtr, "impact_test_temp", None)),
        "impact_coupon_size": _normalize_text(getattr(mtr, "impact_coupon_size", None)),
        "direction": _normalize_text(getattr(mtr, "direction", None)),
        "plate_dimension": derived_thickness,
        "thickness": derived_thickness,
        "dimensions": getattr(inventory, "dimensions", None) if inventory else None,
        "lot_number": getattr(inventory, "lot_number", None) if inventory else getattr(mtr, "batch_number", None),
        "heat_number": getattr(inventory, "heat_number", None) if inventory else getattr(mtr, "heat_number", None),
        "batch_number": getattr(mtr, "batch_number", None),
        "grade": getattr(mtr, "grade", None),
        "manufacturer": getattr(mtr, "manufacturer", None),
        "certificate_number": getattr(mtr, "certificate_number", None),
        "country_of_melt": getattr(mtr, "country_of_melt", None),
        "country_of_manufacture": getattr(mtr, "country_of_manufacture", None),
        "weight": _safe_float(getattr(inventory, "weight", None)) if inventory else None,
        "item_no": getattr(inventory, "item_no", None) if inventory else None,
        "location_code": getattr(inventory, "location_code", None) if inventory else None,
        "description": getattr(inventory, "description", None) if inventory else None,
        "description_2": getattr(inventory, "description_2", None) if inventory else None,
        "document_no": getattr(inventory, "document_no", None) if inventory else None,
    }

    for key, value in mapping.items():
        if field == key:
            return value

    if field in ("thickness", "plate_thickness", "wall_thickness", "plate_dimension"):
        return derived_thickness
    if field in ("temperature", "impact_temperature", "test_temp"):
        return _safe_float(getattr(mtr, "impact_test_temp", None))
    return getattr(mtr, field, None) or (getattr(inventory, field, None) if inventory else None) or mapping.get(field)


def _format_missing_note(field_name, source_label="MTR/inventory"):
    label = (field_name or "").strip()
    if not label:
        return None
    return _("Spec field '%s' was extracted, but no matching field exists in %s.") % (label, source_label)


def _sanitize_missing_notes(notes, mtr, inventory, mtr_values):
    cleaned = []
    if not notes:
        return cleaned
    for note in notes:
        text = (note or "").strip()
        if not text:
            continue
        match = re.search(r"Spec field '([^']+)' was extracted", text, re.IGNORECASE)
        if match:
            field_name = match.group(1).strip()
            if _field_exists_in_candidate(field_name, mtr, inventory, mtr_values):
                continue
        cleaned.append(text)
    return cleaned


def _find_matched_grade_label(grade_value, grade_tokens, branch):
    if not branch:
        return None
    raw_equivalents = []
    raw_equivalents.extend(_split_equivalents(branch.astm_equivalent))
    raw_equivalents.extend(_split_equivalents(branch.grades))
    raw_equivalents.extend(_split_equivalents(branch.manufacturer_grades))
    raw_equivalents.extend(_split_equivalents(branch.approved_substitutes))
    if not raw_equivalents:
        return None

    normalized_grade = _normalize_grade(grade_value)
    normalized_tokens = {_normalize_grade(token) for token in (grade_tokens or []) if token}

    for equivalent in raw_equivalents:
        if not equivalent:
            continue
        normalized_equivalent = _normalize_grade(equivalent)
        if normalized_equivalent and normalized_grade == normalized_equivalent:
            return equivalent
        equivalent_tokens = {_normalize_grade(token) for token in _extract_grade_tokens(equivalent) if token}
        if equivalent_tokens and normalized_tokens and normalized_tokens.intersection(equivalent_tokens):
            return equivalent
    return None


def _collect_missing_field_notes(branch, mtr, inventory, mtr_values):
    notes = []
    if not branch:
        return notes

    for limit in branch.branch_chem_limit_ids:
        element_key = _normalize_text(limit.element)
        if element_key and _field_exists_in_candidate(element_key, mtr, inventory, mtr_values):
            continue
        note = _format_missing_note(element_key)
        if note:
            notes.append(note)

    for line in branch.branch_mech_limit_ids:
        prop = _normalize_text(line.property)
        if prop == "yield":
            value = getattr(mtr, "yield_strength", None)
        elif prop == "tensile":
            value = getattr(mtr, "tensile_strength", None)
        elif prop == "hardness":
            value = getattr(mtr, "hardness", None)
        else:
            value = getattr(mtr, "elongation", None)
        if _safe_float(value) is None:
            note = _format_missing_note(prop)
            if note:
                notes.append(note)

    if branch.branch_impact_limit_ids:
        impact_fields = [
            ("impact_test_temp", getattr(mtr, "impact_test_temp", None)),
            ("impact_coupon_size", getattr(mtr, "impact_coupon_size", None)),
            ("impact_specimen_1", getattr(mtr, "impact_specimen_1", None)),
            ("impact_specimen_2", getattr(mtr, "impact_specimen_2", None)),
            ("impact_specimen_3", getattr(mtr, "impact_specimen_3", None)),
            ("impact_average", getattr(mtr, "impact_average", None)),
        ]
        for field_name, value in impact_fields:
            if value in (None, False, ""):
                note = _format_missing_note(field_name)
                if note:
                    notes.append(note)

    if branch.branch_ce_threshold_ids:
        thickness = _parse_thickness(getattr(inventory, "dimensions", None))
        if thickness is None and _safe_float(getattr(mtr, "thickness", None)) is None:
            note = _format_missing_note("thickness")
            if note:
                notes.append(note)

    return notes


def _field_exists_in_candidate(field_name, mtr, inventory, mtr_values):
    if not field_name:
        return False
    return _rule_subject_from_field(field_name, mtr, inventory, mtr_values) is not None


def _evaluate_custom_rule(rule, mtr, inventory, mtr_values):
    field_name = rule.field_name or rule.label or rule.rule_type
    operator = _normalize_rule_operator(rule.operator or "")
    subject = _rule_subject_from_field(field_name, mtr, inventory, mtr_values)

    if operator in ("exists", "missing"):
        is_missing = subject in (None, False, "")
        if operator == "exists":
            if subject is None:
                return ("n/a", False, False, _format_missing_note(field_name))
            return ("pass" if not is_missing else "fail", False, False, None)
        if subject is None:
            return ("n/a", False, False, _format_missing_note(field_name))
        return ("pass" if is_missing else "fail", False, False, None)

    if subject in (None, False, ""):
        return ("n/a", False, False, _format_missing_note(field_name))

    expected_number = None
    if rule.value_number not in (None, False, ""):
        expected_number = _rule_number_with_unit(rule.value_number, rule.value_unit, field_name)

    if expected_number is not None:
        subject_number = _safe_float(subject)
        if subject_number is None:
            return ("missing", True, False)
        if operator == "=":
            return ("pass" if subject_number == expected_number else "fail", False, False)
        if operator == "!=":
            return ("pass" if subject_number != expected_number else "fail", False, False)
        if operator == ">":
            return ("pass" if subject_number > expected_number else "fail", False, False)
        if operator == ">=":
            return ("pass" if subject_number >= expected_number else "fail", False, False)
        if operator == "<":
            return ("pass" if subject_number < expected_number else "fail", False, False)
        if operator == "<=":
            return ("pass" if subject_number <= expected_number else "fail", False, False)
        if operator == "in":
            return ("pass" if subject_number in [_safe_float(v) for v in _split_rule_values(rule.value_text or rule.value_number)] else "fail", False, False)
        if operator == "not_in":
            return ("pass" if subject_number not in [_safe_float(v) for v in _split_rule_values(rule.value_text or rule.value_number)] else "fail", False, False)
        return ("n/a", False, False, _format_missing_note(field_name))

    subject_text = _normalize_text(subject)
    expected_text = _normalize_text(rule.value_text if rule.value_text not in (None, "") else rule.value_number)
    if operator == "=":
        return ("pass" if subject_text == expected_text else "fail", False, False)
    if operator == "!=":
        return ("pass" if subject_text != expected_text else "fail", False, False)
    if operator == "contains":
        return ("pass" if expected_text and expected_text in subject_text else "fail", False, False)
    if operator == "not_contains":
        return ("pass" if not expected_text or expected_text not in subject_text else "fail", False, False)
    if operator == "starts_with":
        return ("pass" if expected_text and subject_text.startswith(expected_text) else "fail", False, False)
    if operator == "ends_with":
        return ("pass" if expected_text and subject_text.endswith(expected_text) else "fail", False, False)
    if operator == "in":
        options = [_normalize_text(v) for v in _split_rule_values(rule.value_text or rule.value_number)]
        return ("pass" if subject_text in options else "fail", False, False)
    if operator == "not_in":
        options = [_normalize_text(v) for v in _split_rule_values(rule.value_text or rule.value_number)]
        return ("pass" if subject_text not in options else "fail", False, False)

    return ("n/a", False, False, _format_missing_note(field_name))


def _build_custom_rule_ai_context(branch, mtr, inventory, mtr_values):
    rules = branch.branch_custom_rule_ids if branch else []
    return {
        "spec_name": branch.spec_id.name if branch and branch.spec_id else "",
        "branch_key": branch.branch_key if branch else "",
        "branch_name": branch.name if branch else "",
        "selector_summary": branch.selector_summary if branch else "",
        "branch_notes": branch.notes if branch else "",
        "mtr": {
            "batch_number": getattr(mtr, "batch_number", None),
            "heat_number": getattr(mtr, "heat_number", None),
            "grade": getattr(mtr, "grade", None),
            "ce": getattr(mtr, "ce", None),
            "thickness": getattr(mtr, "thickness", None),
            "yield_strength": getattr(mtr, "yield_strength", None),
            "tensile_strength": getattr(mtr, "tensile_strength", None),
            "elongation": getattr(mtr, "elongation", None),
            "hardness": getattr(mtr, "hardness", None),
            "country_of_melt": getattr(mtr, "country_of_melt", None),
            "country_of_manufacture": getattr(mtr, "country_of_manufacture", None),
        },
        "inventory": {
            "lot_number": getattr(inventory, "lot_number", None),
            "heat_number": getattr(inventory, "heat_number", None),
            "dimensions": getattr(inventory, "dimensions", None),
            "weight": getattr(inventory, "weight", None),
            "location_code": getattr(inventory, "location_code", None),
        },
        "mtr_values": mtr_values,
        "custom_rules": [
            {
                "label": rule.label,
                "field_name": rule.field_name,
                "operator": rule.operator,
                "value_text": rule.value_text,
                "value_number": rule.value_number,
                "value_unit": rule.value_unit,
                "description": rule.description,
                "raw_json": rule.raw_json,
            }
            for rule in rules
        ],
    }


def _call_openai_custom_rule_planner(api_key, model, payload):
    system_prompt = (
        "You are the MTR match-time rule planner. "
        "Decide how each custom rule should affect matching for the exact MTR and inventory record provided. "
        "Return ONLY valid JSON with this shape: "
        "{"
        "\"branch_key\":\"\","
        "\"branch_name\":\"\","
        "\"summary\":\"\","
        "\"custom_rule_plan\":[{"
        "\"label\":\"\","
        "\"decision\":\"pass\","
        "\"match_status\":\"pass\","
        "\"reason\":\"\","
        "\"mapped_field\":\"\","
        "\"mapped_operator\":\"\","
        "\"mapped_value_text\":\"\","
        "\"mapped_value_number\":null,"
        "\"mapped_value_unit\":\"\""
        "}],"
        "\"notes\":[\"\"],"
        "\"overall_status\":\"pass\""
        "}. "
        "Allowed decisions are pass, fail, ignore, needs_review. "
        "Use pass/fail only when the rule clearly applies to this specific record. "
        "Use ignore for reference-only text that should not block matching. "
        "Use needs_review when the rule cannot be interpreted safely. "
        "If you can map a rule to a concrete field, include mapped_field and mapped operator/value details. "
    )
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        "temperature": 0.1,
    }
    headers = {
        "Authorization": "Bearer %s" % api_key,
        "Content-Type": "application/json",
    }
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=body,
        timeout=35,
    )
    response.raise_for_status()
    data = response.json()
    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )
    return _extract_json(content), content


def _build_match_ai_context(branch, mtr, inventory, mtr_values):
    def _safe_json(text):
        if not text:
            return {}
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {"value": parsed}
        except Exception:
            return {}

    def _record_fields(record, fields):
        data = {}
        for field_name in fields:
            value = getattr(record, field_name, None)
            if value not in (None, "", False):
                data[field_name] = value
        return data

    spec = branch.spec_id if branch else None
    return {
        "spec": {
            "id": spec.id if spec else None,
            "name": spec.name if spec else "",
            "customer": spec.customer if spec else "",
            "ce_formula": spec.ce_formula if spec else "",
            "notes": spec.notes if spec else "",
        },
        "branch": {
            "id": branch.id if branch else None,
            "branch_key": branch.branch_key if branch else "",
            "name": branch.name if branch else "",
            "spec_type": branch.spec_type if branch else "",
            "selector_summary": branch.selector_summary if branch else "",
            "selector_json": _safe_json(branch.selector_json if branch else ""),
            "branch_json": _safe_json(branch.branch_json if branch else ""),
            "astm_equivalent": branch.astm_equivalent if branch else "",
            "grades": branch.grades if branch else "",
            "manufacturer_grades": branch.manufacturer_grades if branch else "",
            "approved_substitutes": branch.approved_substitutes if branch else "",
            "notes": branch.notes if branch else "",
            "chem_limits": [
                {
                    "element": line.element,
                    "min_value": line.min_value,
                    "max_value": line.max_value,
                    "source": line.source,
                }
                for line in (branch.branch_chem_limit_ids if branch else [])
            ],
            "mech_limits": [
                {
                    "property": line.property,
                    "min_value": line.min_value,
                    "max_value": line.max_value,
                    "unit": line.unit,
                    "specimen_size": line.specimen_size,
                }
                for line in (branch.branch_mech_limit_ids if branch else [])
            ],
            "impact_limits": [
                {
                    "temperature": line.temperature,
                    "coupon_size": line.coupon_size,
                    "min_average": line.min_average,
                    "min_individual": line.min_individual,
                    "unit": line.unit,
                    "min_readings": line.min_readings,
                    "orientation": line.orientation,
                }
                for line in (branch.branch_impact_limit_ids if branch else [])
            ],
            "condition_rules": [
                {
                    "target_element": line.target_element,
                    "condition_element": line.condition_element,
                    "condition_type": line.condition_type,
                    "condition_threshold": line.condition_threshold,
                    "target_adjustment": line.target_adjustment,
                    "target_new_max": line.target_new_max,
                    "description": line.description or "",
                }
                for line in (branch.branch_condition_rule_ids if branch else [])
            ],
            "ce_thresholds": [
                {
                    "thickness_min": line.thickness_min,
                    "thickness_max": line.thickness_max,
                    "max_ce": line.max_ce,
                }
                for line in (branch.branch_ce_threshold_ids if branch else [])
            ],
            "custom_rules": [
                {
                    "rule_type": line.rule_type,
                    "label": line.label,
                    "field_name": line.field_name,
                    "operator": line.operator,
                    "value_text": line.value_text,
                    "value_number": line.value_number,
                    "value_unit": line.value_unit,
                    "description": line.description or "",
                    "raw_json": line.raw_json or "",
                }
                for line in (branch.branch_custom_rule_ids if branch else [])
            ],
        },
        "lookup_policy": {
            "primary_fields": ["grade", "manufacturer"],
            "secondary_fields": ["country_of_melt", "country_of_manufacture", "description", "item_description"],
            "instructions": "Use the extracted branch, the candidate MTR record, and the inventory record as the source of truth. Do not rely on product finish abbreviations or product alias tables for matching.",
        },
        "mtr": _record_fields(mtr, [
            "batch_number",
            "heat_number",
            "certificate_number",
            "grade",
            "manufacturer",
            "country_of_melt",
            "country_of_manufacture",
            "piece_no",
            "c_element",
            "mn_element",
            "si_element",
            "p_element",
            "s_element",
            "cu_element",
            "ni_element",
            "cr_element",
            "mo_element",
            "n_element",
            "v_element",
            "nb_element",
            "ti_element",
            "al_element",
            "ca_element",
            "zr_element",
            "zn_element",
            "sn_element",
            "ce",
            "yield_strength",
            "tensile_strength",
            "elongation",
            "reduction_area",
            "hardness",
            "thickness",
            "impact_test_temp",
            "impact_coupon_size",
            "impact_specimen_1",
            "impact_specimen_2",
            "impact_specimen_3",
            "impact_average",
            "direction",
        ]),
        "inventory": _record_fields(inventory, [
            "lot_number",
            "heat_number",
            "slab_number",
            "item_no",
            "dimensions",
            "quantity",
            "weight",
            "location_code",
            "document_no",
            "grade",
            "posting_date",
            "country_of_melt",
            "country_of_manufacture",
            "description",
            "item_description",
        ]),
        "computed": {
            "mtr_values": mtr_values,
            "thickness_from_inventory": _parse_thickness(getattr(inventory, "dimensions", None)) if inventory else None,
            "thickness_unit": "in",
        },
    }


def _call_openai_match_decider(api_key, model, payload):
    system_prompt = (
        "You are the final MTR matching judge. "
        "Read the extracted specification branch as the source of truth, even if its headers or labels are inconsistent. "
        "Use the full extracted branch data, selector JSON, branch JSON, chemistry/mechanical/impact/CE/condition/custom rules, and the candidate MTR/inventory record. "
        "Do not rely on product finish abbreviations or product alias tables for matching. "
        "Use the extracted branch, the candidate MTR record, and the inventory record as the source of truth. "
        "All thickness values are already normalized to inches in the extracted branch data and record context. "
        "Every extracted branch field that applies to the candidate record must be considered in the decision. "
        "If the branch includes grade equivalence, thickness ranges, chemistry limits, mechanical limits, impact limits, CE thresholds, condition rules, or custom rules, evaluate them all. "
        "Do not ignore a field that is present and applicable just because another field matches. "
        "Decide which parts of the branch are actually applicable for this record and whether the record matches only when all applicable limits pass. "
        "Do not require exact header names if a field is clearly the same concept. "
        "Return ONLY valid JSON with this shape: "
        "{"
        "\"answer\":\"\","
        "\"decision\":\"pass|fail|needs_review\","
        "\"branch_match\":true,"
        "\"confidence\":0,"
        "\"matched_points\":[\"\"],"
        "\"failed_points\":[\"\"],"
        "\"record_fields_used\":[\"\"],"
        "\"reason\":\"\""
        "}. "
        "If the record satisfies the branch, decision must be pass. "
        "If the record clearly fails, decision must be fail. "
        "If there is not enough information, decision must be needs_review. "
        "The answer should be short and plain text."
    )
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        "temperature": 0.1,
    }
    headers = {
        "Authorization": "Bearer %s" % api_key,
        "Content-Type": "application/json",
    }
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=body,
        timeout=35,
    )
    response.raise_for_status()
    data = response.json()
    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )
    return _extract_json(content), content


def _normalize_thickness_unit(unit):
    text = _normalize_text(unit)
    if text in ("mm", "millimeter", "millimeters"):
        return "in"
    if text in ("cm", "centimeter", "centimeters"):
        return "in"
    if text in ("in", "inch", "inches", '"'):
        return "in"
    return "in"


def _normalize_thickness_value(value, unit):
    num = _safe_float(value)
    if num is None:
        return None
    text = _normalize_text(unit)
    if text in ("mm", "millimeter", "millimeters"):
        return _mm_to_in(num)
    if text in ("cm", "centimeter", "centimeters"):
        return _cm_to_in(num)
    return num


def _normalize_temperature_unit(unit):
    text = _normalize_text(unit)
    if text in ("c", "celsius", "deg c", "°c", "celcius"):
        return "f"
    if text in ("f", "fahrenheit", "deg f", "°f"):
        return "f"
    return "f"


def _normalize_temperature_value(value, unit):
    num = _safe_float(value)
    if num is None:
        return None
    text = _normalize_text(unit)
    if text in ("c", "celsius", "deg c", "°c", "celcius"):
        return _c_to_f(num)
    return num


def _ksi_to_mpa(value):
    if value is None:
        return None
    return _round5(value * 6.89476)


def _ksi_to_psi(value):
    if value is None:
        return None
    return _round5(value * 1000.0)


def _mpa_to_ksi(value):
    if value is None:
        return None
    return _round5(value / 6.89476)


def _mpa_to_psi(value):
    if value is None:
        return None
    return _round5(value * 145.0377377)


def _normalize_strength_value(value, source_unit):
    num = _safe_float(value)
    if num is None:
        return None
    unit = _normalize_text(source_unit)
    if unit in ("mpa", "megapascal", "megapascals"):
        return _mpa_to_psi(num)
    if unit in ("ksi", "ks", "kpsi"):
        return _ksi_to_psi(num)
    return num


def _j_to_ftlb(value):
    if value is None:
        return None
    return _round5(value / 1.35582)


def _ftlb_to_j(value):
    if value is None:
        return None
    return _round5(value * 1.35582)


def _mm_to_in(value):
    if value is None:
        return None
    return _round5(value / 25.4)


def _cm_to_in(value):
    if value is None:
        return None
    return _round5(value / 2.54)


def _c_to_f(value):
    if value is None:
        return None
    return _round5((value * 9.0 / 5.0) + 32.0)


def _f_to_c(value):
    if value is None:
        return None
    return _round5((value - 32.0) * 5.0 / 9.0)


class MtrSpecification(models.Model):
    _name = "mtr.specification"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "MTR Specification"
    _rec_name = "name"
    _order = "create_date desc, id desc"

    name = fields.Char(required=True)
    customer = fields.Char()
    status = fields.Selection([
        ("pending", "Pending"),
        ("active", "Active"),
        ("archived", "Archived"),
    ], default="active")

    ce_formula = fields.Text(default="CE = C + Mn/6 + (Cr+Mo+V)/5 + (Ni+Cu)/15")

    branch_ids = fields.One2many("mtr.spec.rule.branch", "spec_id", string="AI Match Branches")

    notes = fields.Text()
    source_pdf = fields.Binary(string="Spec PDF")
    source_pdf_name = fields.Char(string="Spec PDF Name")

    def action_open_match_wizard(self):
        # Keep the button name for compatibility, but open the chatbot UI.
        return self.action_open_chatbot_match()

    def action_open_chatbot_match(self):
        self.ensure_one()
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("mtr_module.last_spec_id.%s" % self.env.user.id, str(self.id))
        params.set_param(
            "mtr_module.pending_match.%s" % self.env.user.id,
            "%s|%s" % (self.id, self.name or ""),
        )
        action = self.env.ref("mtr_module.action_mtr_chatbot").sudo().read()[0]
        action["context"] = {
            "match_spec_id": self.id,
            "match_spec_name": self.name,
            "match_reset_state": True,
        }
        action["params"] = {
            "match_spec_id": self.id,
            "match_spec_name": self.name,
            "match_reset_state": True,
        }
        action["target"] = "current"
        return action

    def action_open_filter_planner(self):
        self.ensure_one()
        key = "mtr_module.last_spec_id.%s" % self.env.user.id
        self.env["ir.config_parameter"].sudo().set_param(key, str(self.id))
        return {
            "type": "ir.actions.client",
            "tag": "mtr_module.mtr_spec_planner_action",
            "name": _("MTR Filter Planner"),
            "context": {
                "planner_mode": True,
                "planner_spec_id": self.id,
                "planner_spec_name": self.name,
            },
            "params": {
                "planner_mode": True,
                "planner_spec_id": self.id,
                "planner_spec_name": self.name,
            },
        }

    @api.model
    def upsert_from_payload(self, payload):
        if not isinstance(payload, dict):
            raise UserError(_("Payload must be a dictionary."))

        spec_id = payload.get("spec_id")
        if isinstance(spec_id, str) and spec_id.strip().isdigit():
            spec_id = int(spec_id.strip())
        spec_name = _clean_spec_name(payload.get("spec_name") or payload.get("name") or "")
        if not spec_id and not spec_name:
            raise UserError(_("spec_name or spec_id is required."))

        values = {
            "name": spec_name or payload.get("spec_code") or payload.get("spec"),
            "customer": payload.get("customer"),
            "ce_formula": payload.get("ce_formula") or self._fields["ce_formula"].default(self),
            "notes": payload.get("notes"),
            "status": payload.get("status") or "active",
        }

        spec = None
        if spec_id:
            spec = self.search([("id", "=", spec_id)], limit=1)
            if not spec:
                raise UserError(_("spec_id %s not found. Pending record may not exist or wrong database.") % spec_id)
        if not spec and not spec_id and spec_name:
            domain = [("name", "ilike", spec_name)]
            if payload.get("customer"):
                domain.append(("customer", "ilike", payload.get("customer")))
            spec = self.search(domain, limit=1)
            # Fallback: if spec_name contains comma, try first token
            if not spec and "," in spec_name:
                first = _clean_spec_name(spec_name.split(",")[0])
                if first:
                    domain = [("name", "ilike", first)]
                    if payload.get("customer"):
                        domain.append(("customer", "ilike", payload.get("customer")))
                    spec = self.search(domain, limit=1)

        if spec:
            # If pending record, prefer AI spec_name to replace placeholder
            if spec.name and spec.name.upper().startswith("PENDING") and spec_name:
                values["name"] = spec_name
                values["status"] = "active"
            spec.write(values)
        else:
            spec = self.create(values)

        spec._replace_lines_from_payload(payload)
        return {"id": spec.id, "operation": "updated" if spec_id or spec_name else "created"}

    def _replace_lines_from_payload(self, payload):
        self.ensure_one()
        def _clear_lines(model):
            self.env[model].search([("spec_id", "=", self.id)]).unlink()

        for model in (
            "mtr.spec.rule.branch",
            "mtr.spec.chem.limit",
            "mtr.spec.mech.limit",
            "mtr.spec.impact.limit",
            "mtr.spec.condition.rule",
            "mtr.spec.ce.threshold",
            "mtr.spec.custom.rule",
        ):
            _clear_lines(model)

        raw_branches = payload.get("branches") if isinstance(payload.get("branches"), list) else []
        if not raw_branches:
            raw_branches = [{
                "branch_key": "branch_1",
                "name": payload.get("branch_name") or payload.get("spec_name") or "Default",
                "selector_summary": payload.get("notes") or "",
                "chem_limits": payload.get("chem_limits") or [],
                "mech_limits": payload.get("mech_limits") or [],
                "impact_limits": payload.get("impact_limits") or [],
                "condition_rules": payload.get("condition_rules") or [],
                "ce_thresholds": payload.get("ce_thresholds") or [],
                "custom_rules": payload.get("custom_rules") or [],
            }]

        def _branch_lines(branch, key):
            lines = branch.get(key)
            if isinstance(lines, list):
                return lines
            return []

        branch_keys = []
        for idx, branch in enumerate(raw_branches):
            if not isinstance(branch, dict):
                continue
            branch_key = _normalize_branch_key(branch.get("branch_key") or branch.get("key") or branch.get("id") or ("branch_%s" % (idx + 1)))
            branch_keys.append(branch_key)
            branch_payload = dict(branch)
            branch_payload.pop("product_forms", None)

            branch_chem_limits = []
            for line in branch.get("chem_limits") or []:
                if isinstance(line, dict):
                    branch_chem_limits.append(line)
            if branch_chem_limits:
                branch_payload["chem_limits"] = branch_chem_limits

            branch_mech_limits = []
            for line in branch.get("mech_limits") or []:
                if isinstance(line, dict):
                    mech_copy = dict(line)
                    raw_unit = (mech_copy.get("unit") or "psi")
                    unit_norm = str(raw_unit).strip().lower()
                    if unit_norm in ("percent", "percentage", "%"):
                        unit_norm = "%"
                    elif unit_norm in ("mpa", "megapascal", "megapascals", "ksi", "ks", "kpsi", "psi"):
                        unit_norm = "psi"
                    elif unit_norm in ("bhn", "brinell", "hbw"):
                        unit_norm = "hbw"
                    else:
                        unit_norm = "psi"
                    raw_prop = (mech_copy.get("property") or "").strip().lower().replace("-", "_").replace(" ", "_")
                    if raw_prop.startswith("elongation"):
                        unit_norm = "%"
                    elif raw_prop in ("reduction_area", "reductionarea", "ra"):
                        unit_norm = "%"
                    elif "hardness" in raw_prop or raw_prop in ("bhn", "brinell", "hbw"):
                        unit_norm = "hbw"
                    else:
                        unit_norm = "psi"
                    mech_copy["unit"] = unit_norm
                    branch_mech_limits.append(mech_copy)
            if branch_mech_limits:
                branch_payload["mech_limits"] = branch_mech_limits

            branch_impact_limits = []
            for line in branch.get("impact_limits") or []:
                if isinstance(line, dict):
                    impact_copy = dict(line)
                    impact_copy["temperature"] = _normalize_temperature_value(impact_copy.get("temperature"), impact_copy.get("temperature_unit"))
                    impact_copy["temperature_unit"] = "f"
                    impact_copy["unit"] = "j"
                    branch_impact_limits.append(impact_copy)
            if branch_impact_limits:
                branch_payload["impact_limits"] = branch_impact_limits

            branch_ce_thresholds = []
            for line in branch.get("ce_thresholds") or []:
                if isinstance(line, dict):
                    ce_copy = dict(line)
                    ce_copy["thickness_min"] = _normalize_thickness_value(ce_copy.get("thickness_min"), ce_copy.get("thickness_unit"))
                    ce_copy["thickness_max"] = _normalize_thickness_value(ce_copy.get("thickness_max"), ce_copy.get("thickness_unit"))
                    ce_copy["thickness_unit"] = "in"
                    branch_ce_thresholds.append(ce_copy)
            if branch_ce_thresholds:
                branch_payload["ce_thresholds"] = branch_ce_thresholds

            branch_custom_rules = []
            for line in branch.get("custom_rules") or branch.get("extra_rules") or []:
                if isinstance(line, dict):
                    custom_copy = dict(line)
                    branch_custom_rules.append(custom_copy)
            if branch_custom_rules:
                branch_payload["custom_rules"] = branch_custom_rules

            self.env["mtr.spec.rule.branch"].create({
                "spec_id": self.id,
                "branch_key": branch_key,
                "name": (branch.get("name") or branch.get("label") or branch_key).strip(),
                "selector_summary": branch.get("selector_summary") or branch.get("reason") or branch.get("description"),
                "spec_type": branch.get("spec_type"),
                "ai_summary": branch.get("ai_summary"),
                "astm_equivalent": ", ".join(_split_equivalents(branch.get("astm_equivalent"))),
                "grades": ", ".join(_split_equivalents(branch.get("grades"))),
                "manufacturer_grades": ", ".join(_split_equivalents(branch.get("manufacturer_grades"))),
                "approved_substitutes": ", ".join(_split_equivalents(branch.get("approved_substitutes"))),
                "notes": branch.get("notes") or payload.get("notes"),
                "selector_json": json.dumps({
                    "spec_type": branch.get("spec_type"),
                    "selector": branch.get("selector"),
                    "thickness_rules": branch.get("thickness_rules"),
                    "grade_rules": branch.get("grade_rules"),
                    "notes": branch.get("notes"),
                }, ensure_ascii=False, sort_keys=True, default=str),
                "branch_json": json.dumps(branch_payload, ensure_ascii=False, sort_keys=True, default=str),
                "sequence": idx + 1,
            })
            branch_rec = self.env["mtr.spec.rule.branch"].search([
                ("spec_id", "=", self.id),
                ("branch_key", "=", branch_key),
            ], limit=1)
            if not branch_rec:
                continue

        def _create_chem(branch_key, line):
            raw_source = (line.get("source") or "table")
            source_norm = str(raw_source).strip().lower()
            if source_norm not in ("table", "footnote"):
                source_norm = "table"
            element = _normalize_text(line.get("element"))
            self.env["mtr.spec.chem.limit"].create({
                "branch_id": branch_rec.id,
                "element": element,
                "min_value": _safe_float(line.get("min")),
                "max_value": _safe_float(line.get("max")),
                "source": source_norm,
            })

        def _create_mech(branch_key, line):
            raw_unit = (line.get("unit") or "ksi")
            source_unit = line.get("source_unit") or line.get("sourceUnit") or raw_unit
            unit_norm = str(raw_unit).strip().lower()
            if unit_norm in ("percent", "percentage", "%"):
                unit_norm = "%"
            elif unit_norm in ("mpa", "megapascal", "megapascals"):
                unit_norm = "psi"
            elif unit_norm in ("ksi", "ks", "kpsi"):
                unit_norm = "psi"
            elif unit_norm in ("bhn", "brinell", "hbw"):
                unit_norm = "hbw"
            else:
                unit_norm = "psi"
            raw_prop = (line.get("property") or "").strip().lower().replace("-", "_").replace(" ", "_")
            for suffix in ("_min", "_max", "_minimum", "_maximum"):
                if raw_prop.endswith(suffix):
                    raw_prop = raw_prop[: -len(suffix)]
            raw_prop = raw_prop.strip("_")
            if raw_prop.startswith("elongation"):
                prop_norm = "elongation"
                unit_norm = "%"
            elif raw_prop in ("reduction_area", "reductionarea", "ra"):
                prop_norm = "reduction_area"
                unit_norm = "%"
            elif "tensile" in raw_prop or raw_prop in ("uts", "ultimate"):
                prop_norm = "tensile"
                unit_norm = "psi"
            elif "yield" in raw_prop or raw_prop in ("ys", "yieldstrength", "yield_strength"):
                prop_norm = "yield"
                unit_norm = "psi"
            elif "hardness" in raw_prop or raw_prop in ("bhn", "brinell"):
                prop_norm = "hardness"
                unit_norm = "hbw"
            elif raw_prop in ("yield", "tensile", "hardness", "elongation"):
                prop_norm = raw_prop
                if prop_norm in ("elongation",):
                    unit_norm = "%"
                elif prop_norm == "hardness":
                    unit_norm = "hbw"
                else:
                    unit_norm = "psi"
            else:
                prop_norm = raw_prop or "yield"
            raw_min = line.get("min")
            raw_max = line.get("max")
            min_value = _normalize_strength_value(raw_min, source_unit if prop_norm in ("yield", "tensile") else raw_unit)
            max_value = _normalize_strength_value(raw_max, source_unit if prop_norm in ("yield", "tensile") else raw_unit)
            def _is_zeroish(v):
                return v in (0, 0.0, "0", "0.0")
            if (raw_max is None or raw_max == "" or _is_zeroish(raw_max)) and (raw_min not in (None, "") and not _is_zeroish(raw_min)):
                max_value = None
            if (raw_min is None or raw_min == "" or _is_zeroish(raw_min)) and (raw_max not in (None, "") and not _is_zeroish(raw_max)):
                min_value = None
            if prop_norm == "hardness":
                min_value = _safe_float(raw_min)
                max_value = _safe_float(raw_max)
            self.env["mtr.spec.mech.limit"].create({
                "branch_id": branch_rec.id,
                "property": prop_norm,
                "min_value": min_value,
                "max_value": max_value,
                "unit": unit_norm,
                "specimen_size": line.get("specimen_size"),
            })

        def _create_impact(branch_key, line):
            raw_unit = (line.get("unit") or "j")
            unit_norm = str(raw_unit).strip().lower()
            if unit_norm in ("ft-lb", "ft-lbs", "ftlb", "ftlbs", "ft lb", "ft lbs", "ft-lbf", "ft lbf"):
                unit_norm = "ft-lbf"
            elif unit_norm in ("j", "joule", "joules"):
                unit_norm = "ft-lbf"
            else:
                unit_norm = "ft-lbf"
            min_average = _safe_float(line.get("min_average"))
            min_individual = _safe_float(line.get("min_individual"))
            if raw_unit and str(raw_unit).strip().lower() in ("j", "joule", "joules"):
                min_average = _j_to_ftlb(min_average) if min_average is not None else None
                min_individual = _j_to_ftlb(min_individual) if min_individual is not None else None
            self.env["mtr.spec.impact.limit"].create({
                "branch_id": branch_rec.id,
                "temperature": _normalize_temperature_value(line.get("temperature"), line.get("temperature_unit")),
                "coupon_size": line.get("coupon_size"),
                "min_average": min_average,
                "min_individual": min_individual,
                "unit": unit_norm,
                "min_readings": int(line.get("min_readings") or 3),
                "orientation": line.get("orientation"),
            })

        def _create_condition(branch_key, line):
            target = _normalize_text(line.get("target_element"))
            cond = _normalize_text(line.get("condition_element"))
            self.env["mtr.spec.condition.rule"].create({
                "branch_id": branch_rec.id,
                "target_element": target,
                "condition_element": cond,
                "condition_type": line.get("condition_type"),
                "condition_threshold": _safe_float(line.get("condition_threshold")),
                "target_adjustment": _safe_float(line.get("target_adjustment")),
                "target_new_max": _safe_float(line.get("target_new_max")),
                "description": line.get("description"),
            })

        def _create_ce(branch_key, line):
            unit = line.get("thickness_unit")
            self.env["mtr.spec.ce.threshold"].create({
                "branch_id": branch_rec.id,
                "thickness_min": _normalize_thickness_value(line.get("thickness_min"), unit),
                "thickness_max": _normalize_thickness_value(line.get("thickness_max"), unit),
                "max_ce": _safe_float(line.get("max_ce")),
            })

        for idx, branch in enumerate(raw_branches):
            if not isinstance(branch, dict):
                continue
            branch_key = _normalize_branch_key(branch.get("branch_key") or branch.get("key") or branch.get("id") or ("branch_%s" % (idx + 1)))
            branch_rec = self.env["mtr.spec.rule.branch"].search([
                ("spec_id", "=", self.id),
                ("branch_key", "=", branch_key),
            ], limit=1)
            for line in _branch_lines(branch, "chem_limits"):
                if isinstance(line, dict):
                    _create_chem(branch_key, line)
            for line in _branch_lines(branch, "mech_limits"):
                if isinstance(line, dict):
                    _create_mech(branch_key, line)
            for line in _branch_lines(branch, "impact_limits"):
                if isinstance(line, dict):
                    _create_impact(branch_key, line)
            for line in _branch_lines(branch, "condition_rules"):
                if isinstance(line, dict):
                    _create_condition(branch_key, line)
            for line in _branch_lines(branch, "ce_thresholds"):
                if isinstance(line, dict):
                    _create_ce(branch_key, line)
            for line in _branch_lines(branch, "custom_rules"):
                if isinstance(line, dict):
                    self.env["mtr.spec.custom.rule"].create({
                        "branch_id": branch_rec.id,
                        "rule_type": line.get("rule_type") or line.get("type") or line.get("category") or "custom",
                        "label": line.get("label") or line.get("name") or line.get("title") or line.get("field") or "Custom Rule",
                        "field_name": line.get("field_name") or line.get("field") or line.get("target_field"),
                        "operator": line.get("operator") or line.get("comparison") or line.get("condition"),
                        "value_text": line.get("value_text") or line.get("value") or line.get("expected_value") or line.get("text"),
                        "value_number": _safe_float(line.get("value_number") or line.get("value") or line.get("expected_value")),
                        "value_unit": line.get("value_unit") or line.get("unit"),
                        "description": line.get("description") or line.get("notes"),
                        "raw_json": json.dumps(line, ensure_ascii=False, sort_keys=True, default=str),
                    })

    def _get_conditioned_max(self, element_key, base_max, mtr_values, branch):
        if base_max is None:
            base_max_value = None
        else:
            base_max_value = _round5(base_max)

        adjusted = base_max_value
        rules = branch.branch_condition_rule_ids.filtered(lambda r: r.target_element == element_key) if branch else self.env["mtr.spec.condition.rule"]
        for rule in rules:
            cond_value = mtr_values.get(rule.condition_element)
            if cond_value is None:
                continue
            cond_limit = branch.branch_chem_limit_ids.filtered(lambda l: l.element == rule.condition_element) if branch else self.env["mtr.spec.chem.limit"]
            cond_baseline = cond_limit[:1].max_value if cond_limit else None
            step = rule.condition_threshold or 0.0
            target_adjustment = rule.target_adjustment or 0.0
            if rule.condition_type == "below":
                if cond_value <= (rule.condition_threshold or cond_value):
                    adjusted = rule.target_new_max or (
                        (base_max_value or 0.0) + target_adjustment
                    )
            elif rule.condition_type == "above":
                if cond_value >= (rule.condition_threshold or cond_value):
                    adjusted = rule.target_new_max or (
                        (base_max_value or 0.0) + target_adjustment
                    )
            elif rule.condition_type in ("decrease_by", "increase_by"):
                baseline = cond_baseline
                if baseline is None or step <= 0:
                    continue
                if rule.condition_type == "decrease_by" and cond_value < baseline:
                    steps = math.floor((baseline - cond_value) / step)
                    adjusted = (base_max_value or 0.0) + (steps * target_adjustment)
                if rule.condition_type == "increase_by" and cond_value > baseline:
                    steps = math.floor((cond_value - baseline) / step)
                    adjusted = (base_max_value or 0.0) + (steps * target_adjustment)
            if rule.target_new_max and adjusted is not None:
                adjusted = min(adjusted, rule.target_new_max)

        return _round5(adjusted)

    def _compute_ce(self, mtr_values):
        required = ["c", "mn", "cr", "mo", "ni", "cu"]
        for key in required:
            if mtr_values.get(key) is None:
                return None
        c = mtr_values.get("c") or 0.0
        mn = mtr_values.get("mn") or 0.0
        cr = mtr_values.get("cr") or 0.0
        mo = mtr_values.get("mo") or 0.0
        v = mtr_values.get("v") or 0.0
        ni = mtr_values.get("ni") or 0.0
        cu = mtr_values.get("cu") or 0.0
        return _round5(c + (mn / 6.0) + ((cr + mo + v) / 5.0) + ((ni + cu) / 15.0))


class MtrSpecChemLimit(models.Model):
    _name = "mtr.spec.chem.limit"
    _description = "Spec Chemistry Limit"
    _order = "element asc"

    branch_id = fields.Many2one("mtr.spec.rule.branch", required=True, ondelete="cascade")
    spec_id = fields.Many2one("mtr.specification", related="branch_id.spec_id", store=True, readonly=True)
    element = fields.Char(required=True)
    min_value = fields.Float(digits=(16, 5))
    max_value = fields.Float(digits=(16, 5))
    source = fields.Char(default="table")


class MtrSpecConditionRule(models.Model):
    _name = "mtr.spec.condition.rule"
    _description = "Spec Conditional Rule"
    _order = "id asc"

    branch_id = fields.Many2one("mtr.spec.rule.branch", required=True, ondelete="cascade")
    spec_id = fields.Many2one("mtr.specification", related="branch_id.spec_id", store=True, readonly=True)
    target_element = fields.Char(required=True)
    condition_element = fields.Char(required=True)
    condition_type = fields.Char(required=True)
    condition_threshold = fields.Float(digits=(16, 5), help="Step size or threshold based on condition type.")
    target_adjustment = fields.Float(digits=(16, 5), help="Adjustment per step or flat adjustment.")
    target_new_max = fields.Float(digits=(16, 5), help="Absolute ceiling for the target element.")
    description = fields.Text()


class MtrSpecMechLimit(models.Model):
    _name = "mtr.spec.mech.limit"
    _description = "Spec Mechanical Limit"
    _order = "property asc"

    branch_id = fields.Many2one("mtr.spec.rule.branch", required=True, ondelete="cascade")
    spec_id = fields.Many2one("mtr.specification", related="branch_id.spec_id", store=True, readonly=True)
    property = fields.Char(required=True)
    min_value = fields.Float(digits=(16, 5))
    max_value = fields.Float(digits=(16, 5))
    unit = fields.Char(default="ksi")
    specimen_size = fields.Char()


class MtrSpecImpactLimit(models.Model):
    _name = "mtr.spec.impact.limit"
    _description = "Spec Impact Limit"
    _order = "id asc"

    branch_id = fields.Many2one("mtr.spec.rule.branch", required=True, ondelete="cascade")
    spec_id = fields.Many2one("mtr.specification", related="branch_id.spec_id", store=True, readonly=True)
    temperature = fields.Float(digits=(16, 5), help="Requirement temperature (C).")
    coupon_size = fields.Char()
    min_average = fields.Float(digits=(16, 5))
    min_individual = fields.Float(digits=(16, 5))
    unit = fields.Char(default="j")
    min_readings = fields.Integer(default=3)
    orientation = fields.Char()


class MtrSpecCeThreshold(models.Model):
    _name = "mtr.spec.ce.threshold"
    _description = "Spec Carbon Equivalency Threshold"

    branch_id = fields.Many2one("mtr.spec.rule.branch", required=True, ondelete="cascade")
    spec_id = fields.Many2one("mtr.specification", related="branch_id.spec_id", store=True, readonly=True)
    thickness_min = fields.Float(digits=(16, 5), help="Minimum thickness (inches).")
    thickness_max = fields.Float(digits=(16, 5), help="Maximum thickness (inches).")
    max_ce = fields.Float(digits=(16, 5), required=True)


class MtrSpecCustomRule(models.Model):
    _name = "mtr.spec.custom.rule"
    _description = "Spec Custom Rule"
    _order = "id asc"

    branch_id = fields.Many2one("mtr.spec.rule.branch", required=True, ondelete="cascade")
    spec_id = fields.Many2one("mtr.specification", related="branch_id.spec_id", store=True, readonly=True)
    rule_type = fields.Char(required=True, default="custom")
    label = fields.Char(required=True)
    field_name = fields.Char()
    operator = fields.Char()
    value_text = fields.Text()
    value_number = fields.Float(digits=(16, 5))
    value_unit = fields.Char()
    description = fields.Text()
    raw_json = fields.Text()


class MtrSpecRuleBranch(models.Model):
    _name = "mtr.spec.rule.branch"
    _description = "AI Spec Rule Branch"
    _order = "sequence asc, id asc"

    spec_id = fields.Many2one("mtr.specification", required=True, ondelete="cascade")
    branch_key = fields.Char(required=True, index=True)
    name = fields.Char(required=True)
    spec_type = fields.Char()
    ai_summary = fields.Text()
    astm_equivalent = fields.Text()
    grades = fields.Text()
    manufacturer_grades = fields.Text()
    approved_substitutes = fields.Text()
    notes = fields.Text()
    selector_summary = fields.Text()
    selector_json = fields.Text()
    branch_json = fields.Text()
    sequence = fields.Integer(default=10)
    branch_chem_limit_ids = fields.One2many("mtr.spec.chem.limit", "branch_id", string="Chemistry Limits")
    branch_mech_limit_ids = fields.One2many("mtr.spec.mech.limit", "branch_id", string="Mechanical Limits")
    branch_impact_limit_ids = fields.One2many("mtr.spec.impact.limit", "branch_id", string="Impact Limits")
    branch_condition_rule_ids = fields.One2many("mtr.spec.condition.rule", "branch_id", string="Conditional Rules")
    branch_ce_threshold_ids = fields.One2many("mtr.spec.ce.threshold", "branch_id", string="CE Thresholds")
    branch_custom_rule_ids = fields.One2many("mtr.spec.custom.rule", "branch_id", string="Custom Rules")


class MtrSpecUploadWizard(models.TransientModel):
    _name = "mtr.spec.upload.wizard"
    _description = "Spec PDF Upload Wizard"

    file_data = fields.Binary(required=False)
    file_name = fields.Char(required=False)
    file_ids = fields.Many2many(
        "ir.attachment",
        "mtr_spec_upload_wizard_attachment_rel",
        "wizard_id",
        "attachment_id",
        string="Spec Files",
        help="Upload one or more spec PDFs.",
    )
    spec_name = fields.Char(required=False)
    customer = fields.Char()
    webhook_url = fields.Char(
        default=lambda self: self.env["ir.config_parameter"].sudo().get_param(
            "mtr_module.spec_n8n_webhook_url"
        ) or "https://innovation.eoxs.com/webhook/spec-upload"
    )

    def action_submit_spec(self):
        self.ensure_one()
        if not self.webhook_url:
            raise UserError(_("Please configure spec webhook URL first."))

        files = []
        for attachment in self.file_ids:
            if attachment.datas:
                files.append({
                    "file_name": attachment.name or "spec.pdf",
                    "file_data": attachment.datas,
                })
        if not files and self.file_data:
            files.append({
                "file_name": self.file_name or "spec.pdf",
                "file_data": self.file_data,
            })
        if not files:
            raise UserError(_("Please upload at least one file."))

        first_spec = None
        for idx, f in enumerate(files):
            file_name = f["file_name"]
            file_data = f["file_data"]

            pending_name = self.spec_name if (self.spec_name and len(files) == 1) else ""
            if not pending_name:
                stamp = fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                base = file_name or "Spec PDF"
                pending_name = f"PENDING {base} {stamp}"

            spec = self.env["mtr.specification"].with_context(mail_create_nolog=True).create({
                "name": pending_name,
                "customer": self.customer,
                "status": "pending" if not self.spec_name else "active",
            })
            if not first_spec:
                first_spec = spec

            attachment = self.env["ir.attachment"].create(
                {
                    "name": file_name or "Spec.pdf",
                    "res_model": "mtr.specification",
                    "res_id": spec.id,
                    "type": "binary",
                    "datas": file_data,
                    "mimetype": "application/pdf",
                }
            )
            spec.sudo().message_post(
                body="Spec PDF uploaded",
                attachment_ids=[attachment.id],
                message_type="comment",
                subtype_id=self.env.ref("mail.mt_note").id,
            )

            payload = {
                "source": "odoo13_mtr_module",
                "wizard_id": self.id,
                "spec_name": spec.name,
                "file_name": file_name,
                "file_data": file_data.decode("utf-8") if isinstance(file_data, bytes) else file_data,
                "db_name": self.env.cr.dbname,
            }

            # Send to n8n for parsing.
            self.env["mtr.spec.upload.wizard"]._post_payload(self.webhook_url, payload)

        if not first_spec:
            raise UserError(_("No specs were created."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Specification"),
            "res_model": "mtr.specification",
            "view_mode": "form",
            "res_id": first_spec.id,
        }

    @api.model
    def _post_payload(self, webhook_url, payload):
        from .models import _post_payload_to_n8n  # reuse helper
        _post_payload_to_n8n(webhook_url, payload)




class MtrSpecMatchWizard(models.TransientModel):
    _name = "mtr.spec.match.wizard"
    _description = "Specification Match Wizard"

    spec_id = fields.Many2one("mtr.specification", required=True)
    branch_id = fields.Many2one(
        "mtr.spec.rule.branch",
        domain="[('spec_id', '=', spec_id)]",
        string="AI Branch",
    )
    result_ids = fields.One2many("mtr.spec.match.result", "wizard_id", string="Results")

    @api.onchange("spec_id")
    def _onchange_spec_id(self):
        for wizard in self:
            wizard.branch_id = False
            if wizard.spec_id and len(wizard.spec_id.branch_ids) == 1:
                wizard.branch_id = wizard.spec_id.branch_ids[0]

    def _get_selected_branch(self):
        self.ensure_one()
        spec = self.spec_id
        branches = spec.branch_ids.sorted(lambda b: (b.sequence or 10, b.id))
        if self.branch_id and self.branch_id.spec_id == spec:
            return self.branch_id
        if len(branches) == 1:
            return branches[0]
        if branches:
            raise UserError(
                _("This spec has multiple AI branches. Please select one before matching: %s")
                % ", ".join(branches.mapped("name"))
            )
        return None

    def action_run_match(self):
        self.ensure_one()
        self._run_match_engine(chem_only=False)
        return {"type": "ir.actions.do_nothing"}

    def _run_match_engine(self, chem_only=False):
        self.ensure_one()
        self.env["mtr.spec.match.result"].search([("wizard_id", "=", self.id)]).unlink()
        selected_branch = self._get_selected_branch()

        cr = self.env.cr

        cr.execute("SELECT COUNT(*) FROM mtr_data")
        if not cr.fetchone()[0]:
            raise UserError("No MTR records to match.")

        # Use raw SQL to build lookup maps — avoids creating 200k ORM objects.
        # Only fetch the 4 key columns needed for matching; IDs are stored in maps.
        # Normalize keys inside SQL — eliminates Python regex calls for 200k rows
        cr.execute("""
            SELECT id,
                   UPPER(REGEXP_REPLACE(COALESCE(heat_number, ''),  '[^A-Z0-9]', '', 'g')) AS heat,
                   UPPER(REGEXP_REPLACE(COALESCE(lot_number, ''),   '[^A-Z0-9]', '', 'g')) AS lot,
                   UPPER(REGEXP_REPLACE(COALESCE(slab_number, ''),  '[^A-Z0-9]', '', 'g')) AS slab,
                   UPPER(REGEXP_REPLACE(COALESCE(image_path, ''),   '[^A-Z0-9]', '', 'g')) AS img
            FROM inventory
        """)
        rows = cr.fetchall()
        if not rows:
            raise UserError("No inventory records to match.")

        inv_by_heat = defaultdict(list)
        inv_by_lot = defaultdict(list)
        inv_by_slab = defaultdict(list)
        inv_by_image = defaultdict(list)

        for inv_id, heat, lot, slab, img in rows:
            if heat:
                inv_by_heat[heat].append(inv_id)
            if lot:
                inv_by_lot[lot].append(inv_id)
            if slab:
                inv_by_slab[slab].append(inv_id)
            if img:
                inv_by_image[img].append(inv_id)

        branch_equivalents = []
        if selected_branch:
            if selected_branch.spec_id and selected_branch.spec_id.name:
                branch_equivalents.append(selected_branch.spec_id.name)
            branch_equivalents.extend(_split_equivalents(selected_branch.astm_equivalent))
            branch_equivalents.extend(_split_equivalents(selected_branch.grades))
            branch_equivalents.extend(_split_equivalents(selected_branch.manufacturer_grades))
            branch_equivalents.extend(_split_equivalents(selected_branch.approved_substitutes))
        equivalents = [_normalize_grade(e) for e in branch_equivalents if e]
        equivalents = [_normalize_grade(e) for e in equivalents if e]
        equivalent_tokens = set()
        for e in equivalents:
            for tok in _extract_grade_tokens(e):
                equivalent_tokens.add(_normalize_grade(tok))

        params = self.env["ir.config_parameter"].sudo()
        api_key = params.get_param("mtr_module.openai_api_key")
        model = params.get_param("mtr_module.openai_model") or "gpt-4o-mini"

        # Use raw SQL to get only the MTR fields needed for matching — avoids
        # loading full ORM objects for every record. We only browse() the small
        # subset of MTRs that have actual inventory matches.
        chem_fields = list(_ELEMENT_FIELD_MAP.values())
        mech_fields = ["yield_strength", "tensile_strength", "hardness", "elongation"]
        impact_fields = ["impact_coupon_size", "impact_test_temp",
                         "impact_specimen_1", "impact_specimen_2",
                         "impact_specimen_3", "impact_average"]
        key_fields = ["id", "grade", "heat_number", "batch_number", "certificate_number"]
        all_fields = key_fields + chem_fields + mech_fields + impact_fields
        col_sql = ", ".join(all_fields)
        cr.execute("SELECT %s FROM mtr_data" % col_sql)
        mtr_rows = cr.fetchall()
        col_index = {name: i for i, name in enumerate(all_fields)}

        created = 0
        result_vals_list = []
        for row in mtr_rows:
            mtr_id = row[col_index["id"]]
            mtr_grade = row[col_index["grade"]] or ""
            mtr_heat = _normalize_heat(row[col_index["heat_number"]])
            mtr_batch = _normalize_heat(row[col_index["batch_number"]])
            mtr_cert = _normalize_heat(row[col_index["certificate_number"]])

            # Grade filter
            grade_value = _normalize_grade(mtr_grade)
            grade_tokens = [_normalize_grade(t) for t in _extract_grade_tokens(mtr_grade)]
            grade_match = False
            matched_grade_label = None
            if equivalents:
                if grade_value in equivalents:
                    grade_match = True
                elif equivalent_tokens and any(t in equivalent_tokens for t in grade_tokens):
                    grade_match = True
                if not grade_match:
                    continue

            # Inventory lookup first — skip all expensive checks if no match
            matched_ids = set()
            if mtr_cert:
                matched_ids.update(inv_by_image.get(mtr_cert, []))
            if mtr_batch:
                matched_ids.update(inv_by_slab.get(mtr_batch, []))
            if mtr_heat:
                matched_ids.update(inv_by_heat.get(mtr_heat, []))
            if mtr_batch:
                matched_ids.update(inv_by_lot.get(mtr_batch, []))
            if not matched_ids:
                continue

            # Only browse() the single MTR record now that we know it has matches
            mtr = self.env["mtr.data"].browse(mtr_id)
            if grade_match:
                matched_grade_label = _find_matched_grade_label(mtr_grade, grade_tokens, selected_branch)

            mtr_values = {key: _safe_float(row[col_index[field]])
                          for key, field in _ELEMENT_FIELD_MAP.items()}

            chem_status, _, _ = self._check_chemistry(selected_branch, mtr_values)
            if chem_only:
                mech_status = impact_status = "n/a"
            else:
                mech_status, _, _ = self._check_mechanical(selected_branch, mtr)
                impact_status, _ = self._check_impact(selected_branch, mtr)

            inv_list = self.env["inventory.record"].browse(list(matched_ids))

            for inv in inv_list:
                missing_notes = []
                if chem_only:
                    ce_status, ce_value, ce_max = "n/a", None, None
                    custom_status, custom_note = "n/a", None
                else:
                    ce_status, _, ce_value, ce_max = self._check_ce(selected_branch, mtr_values, inv)
                    custom_status, _, custom_note = self._check_custom_rules(selected_branch, mtr, inv, mtr_values, api_key=api_key, model=model)
                    if custom_note:
                        missing_notes.append(custom_note)

                applicable_statuses = [chem_status]
                if not chem_only:
                    applicable_statuses.extend([mech_status, impact_status, custom_status, ce_status])
                strict_match = all(s in ("pass", "n/a") for s in applicable_statuses)
                if equivalents:
                    strict_match = strict_match and grade_match

                if strict_match:
                    result_vals_list.append({
                        "wizard_id": self.id,
                        "mtr_id": mtr.id,
                        "inventory_id": inv.id,
                        "grade_match": grade_match,
                        "matched_grade_label": matched_grade_label,
                        "chem_status": chem_status,
                        "mech_status": mech_status,
                        "impact_status": impact_status if (not chem_only and selected_branch and selected_branch.branch_impact_limit_ids) else "n/a",
                        "custom_status": custom_status if (not chem_only and selected_branch and selected_branch.branch_custom_rule_ids) else "n/a",
                        "ce_status": ce_status if (not chem_only and selected_branch and selected_branch.branch_ce_threshold_ids) else "n/a",
                        "ce_value": ce_value,
                        "ce_max": ce_max,
                        "missing_notes": " | ".join([n for n in missing_notes if n]),
                    })
                    created += 1
                    continue

                # Code check failed — call AI only for this borderline case
                if not (api_key and selected_branch):
                    continue
                try:
                    match_payload = _build_match_ai_context(selected_branch, mtr, inv, mtr_values)
                    parsed, _ = _call_openai_match_decider(api_key, model, match_payload)
                    decision = _normalize_text((parsed or {}).get("decision"))
                    if decision != "pass":
                        continue
                    ai_notes = []
                    matched_points = parsed.get("matched_points") if isinstance(parsed, dict) else []
                    failed_points = parsed.get("failed_points") if isinstance(parsed, dict) else []
                    reason = (parsed.get("reason") or parsed.get("answer") or "") if isinstance(parsed, dict) else ""
                    if matched_points:
                        ai_notes.append(_("AI matched: %s") % ", ".join([str(p) for p in matched_points if p]))
                    if failed_points:
                        ai_notes.append(_("AI failed points: %s") % ", ".join([str(p) for p in failed_points if p]))
                    if reason:
                        ai_notes.append(reason)
                    if ai_notes:
                        missing_notes.append(" | ".join(ai_notes))
                    result_vals_list.append({
                        "wizard_id": self.id,
                        "mtr_id": mtr.id,
                        "inventory_id": inv.id,
                        "grade_match": True,
                        "matched_grade_label": matched_grade_label,
                        "chem_status": chem_status,
                        "mech_status": mech_status,
                        "impact_status": impact_status,
                        "custom_status": custom_status,
                        "ce_status": ce_status,
                        "ce_value": ce_value,
                        "ce_max": ce_max,
                        "missing_notes": " | ".join([n for n in missing_notes if n]),
                    })
                    created += 1
                except Exception as exc:
                    _logger.warning("AI spec match failed: %s", exc)

        if result_vals_list:
            self.env["mtr.spec.match.result"].create(result_vals_list)

        return created

    def _check_chemistry(self, branch, mtr_values):
        near_miss = False
        checked = False
        limits = branch.branch_chem_limit_ids if branch else self.env["mtr.spec.chem.limit"]
        for limit in limits:
            value = mtr_values.get(limit.element)
            if value is None:
                continue
            checked = True
            max_allowed = branch.spec_id._get_conditioned_max(limit.element, limit.max_value, mtr_values, branch) if branch else None
            if limit.min_value not in (None, False) and value < limit.min_value:
                return "fail", False, near_miss
            if max_allowed is not None and value > max_allowed:
                return "fail", False, near_miss
            if limit.min_value not in (None, False) and value <= (limit.min_value * 1.05):
                near_miss = True
            if max_allowed is not None and value >= (max_allowed * 0.95):
                near_miss = True
        if not checked:
            return "n/a", False, False
        return "pass", False, near_miss

    def _check_mechanical(self, branch, mtr):
        near_miss = False
        checked = False
        lines = branch.branch_mech_limit_ids if branch else self.env["mtr.spec.mech.limit"]
        for line in lines:
            if line.property == "yield":
                value = mtr.yield_strength
            elif line.property == "tensile":
                value = mtr.tensile_strength
            elif line.property == "hardness":
                value = mtr.hardness
            else:
                value = mtr.elongation

            value = _safe_float(value)
            if value is None:
                continue
            checked = True

            min_value = line.min_value
            max_value = line.max_value
            # Some rows store 0.0 instead of NULL; treat 0 as "not provided"
            if (max_value in (0, 0.0)) and (min_value not in (None, 0, 0.0)):
                max_value = None
            if (min_value in (0, 0.0)) and (max_value not in (None, 0, 0.0)):
                min_value = None
            if line.unit == "mpa":
                min_value = _mpa_to_psi(min_value) if min_value is not None else None
                max_value = _mpa_to_psi(max_value) if max_value is not None else None
            elif line.unit == "ksi":
                min_value = _ksi_to_psi(min_value) if min_value is not None else None
                max_value = _ksi_to_psi(max_value) if max_value is not None else None

            if min_value is not None and value < min_value:
                return "fail", False, near_miss
            if max_value is not None and value > max_value:
                return "fail", False, near_miss

            if min_value is not None and value <= (min_value * 1.05):
                near_miss = True
            if max_value is not None and value >= (max_value * 0.95):
                near_miss = True

        if not checked:
            return "n/a", False, False
        return "pass", False, near_miss

    def _check_custom_rules(self, branch, mtr, inventory, mtr_values, api_key=None, model=None):
        rules = branch.branch_custom_rule_ids if branch else self.env["mtr.spec.custom.rule"]
        if not rules:
            return "n/a", False, None

        if api_key is None:
            params = self.env["ir.config_parameter"].sudo()
            api_key = params.get_param("mtr_module.openai_api_key")
            model = params.get_param("mtr_module.openai_model") or "gpt-4o-mini"
        if api_key:
            try:
                payload = _build_custom_rule_ai_context(branch, mtr, inventory, mtr_values)
                parsed, _raw = _call_openai_custom_rule_planner(api_key, model, payload)
                plan_items = (parsed or {}).get("custom_rule_plan") if isinstance(parsed, dict) else None
                if isinstance(plan_items, list) and plan_items:
                    checked = False
                    for item in plan_items:
                        if not isinstance(item, dict):
                            continue
                        decision = _normalize_text(item.get("decision") or item.get("match_status"))
                        if decision in ("ignore", "note", "soft_filter"):
                            continue
                        if decision in ("needs_review", "review", "missing"):
                            continue
                        if decision in ("pass", "fail"):
                            checked = True
                            if decision == "fail":
                                return "fail", False, None
                            continue
                    if checked:
                        return "pass", False, None
                    return "n/a", False, None
            except Exception as exc:
                _logger.warning("AI custom-rule planner failed, falling back to code rules: %s", exc)

        checked = False
        notes = []
        for rule in rules.sorted(lambda r: (r.id or 0)):
            status, missing, _, note = _evaluate_custom_rule(rule, mtr, inventory, mtr_values)
            if note:
                notes.append(note)
            if status == "fail":
                return "fail", False, " | ".join([n for n in notes if n]) or None
            if status == "pass":
                checked = True

        if checked:
            return "pass", False, " | ".join([n for n in notes if n]) or None
        return "n/a", False, " | ".join([n for n in notes if n]) or None

    def _check_impact(self, branch, mtr):
        limits = branch.branch_impact_limit_ids if branch else self.env["mtr.spec.impact.limit"]
        if not limits:
            return "n/a", False

        # Match by coupon size when possible; otherwise use first line.
        line = None
        if mtr.impact_coupon_size:
            coupon = _normalize_text(mtr.impact_coupon_size)
            for candidate in limits:
                if _normalize_text(candidate.coupon_size) == coupon:
                    line = candidate
                    break
        if not line:
            line = limits[:1]
        if not line:
            return "n/a", False

        temp = _safe_float(mtr.impact_test_temp)
        if temp is None:
            return "n/a", False
        if line.temperature is not None and temp > line.temperature:
            return "fail", False

        specimens = [
            _safe_float(mtr.impact_specimen_1),
            _safe_float(mtr.impact_specimen_2),
            _safe_float(mtr.impact_specimen_3),
        ]
        specimens = [v for v in specimens if v is not None]
        if len(specimens) < (line.min_readings or 3):
            return "n/a", False

        avg = _safe_float(mtr.impact_average)
        if avg is None and specimens:
            avg = _round5(sum(specimens) / len(specimens))

        min_avg = line.min_average
        min_individual = line.min_individual
        if line.unit == "j":
            min_avg = _j_to_ftlb(min_avg) if min_avg is not None else None
            min_individual = _j_to_ftlb(min_individual) if min_individual is not None else None

        if min_avg is not None and avg is not None and avg < min_avg:
            return "fail", False
        if min_individual is not None:
            for value in specimens:
                if value < min_individual:
                    return "fail", False

        return "pass", False

    def _check_ce(self, branch, mtr_values, inventory):
        thresholds_qs = branch.branch_ce_threshold_ids if branch else self.env["mtr.spec.ce.threshold"]
        if not thresholds_qs:
            return "n/a", False, None, None
        ce_value = branch.spec_id._compute_ce(mtr_values) if branch else None
        if ce_value is None:
            return "n/a", False, None, None
        thickness = _parse_thickness(inventory.dimensions)
        max_ce = None
        thresholds = thresholds_qs.sorted(lambda t: (t.thickness_min or 0.0, t.thickness_max or 9999))
        for threshold in thresholds:
            if threshold.thickness_min and thickness is not None and thickness < threshold.thickness_min:
                continue
            if threshold.thickness_max and thickness is not None and thickness > threshold.thickness_max:
                continue
            max_ce = threshold.max_ce
            break
        if max_ce is None:
            return "n/a", False, ce_value, None
        if ce_value > max_ce:
            return "fail", False, ce_value, max_ce
        return "pass", False, ce_value, max_ce


class MtrSpecMatchResult(models.TransientModel):
    _name = "mtr.spec.match.result"
    _description = "Spec Match Result"
    _order = "id asc"

    wizard_id = fields.Many2one("mtr.spec.match.wizard", required=True, ondelete="cascade")
    mtr_id = fields.Many2one("mtr.data", required=True)
    inventory_id = fields.Many2one("inventory.record", required=True)

    grade_match = fields.Boolean()
    matched_grade_label = fields.Char()

    chem_status = fields.Selection([("pass", "Pass"), ("fail", "Fail"), ("missing", "Missing"), ("n/a", "N/A")])
    mech_status = fields.Selection([("pass", "Pass"), ("fail", "Fail"), ("missing", "Missing"), ("n/a", "N/A")])
    impact_status = fields.Selection([("pass", "Pass"), ("fail", "Fail"), ("missing", "Missing"), ("n/a", "N/A")])
    custom_status = fields.Selection([("pass", "Pass"), ("fail", "Fail"), ("missing", "Missing"), ("n/a", "N/A")])
    ce_status = fields.Selection([("pass", "Pass"), ("fail", "Fail"), ("missing", "Missing"), ("n/a", "N/A")])

    ce_value = fields.Float(digits=(16, 5))
    ce_max = fields.Float(digits=(16, 5))
    missing_notes = fields.Char()

    batch_number = fields.Char(related="mtr_id.batch_number", readonly=True)
    grade = fields.Char(related="mtr_id.grade", readonly=True)
    lot_number = fields.Char(related="inventory_id.lot_number", readonly=True)
    dimensions = fields.Char(related="inventory_id.dimensions", readonly=True)
    weight = fields.Float(digits=(16, 5), related="inventory_id.weight", readonly=True)
    location = fields.Char(related="inventory_id.location_code", readonly=True)
