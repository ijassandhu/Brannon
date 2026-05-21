# -*- coding: utf-8 -*-
import json
import logging
import re

import requests

from odoo import http, _
from odoo.http import request

_logger = logging.getLogger(__name__)

_FIELD_MAP = {
    "heat_number": "mtr_heat_number",
    "batch_number": "mtr_batch_number",
    "grade": "mtr_grade",
    "manufacturer": "mtr_manufacturer",
    "certificate_number": "mtr_certificate_number",
    "certificate_date": "mtr_certificate_date",
    "country_of_melt": "mtr_country_of_melt",
    "country_of_manufacture": "mtr_country_of_manufacture",
    "piece_no": "mtr_piece_no",
    "lot_number": "inv_lot_number",
    "item_no": "inv_item_no",
    "slab_number": "inv_slab_number",
    "inventory_heat_number": "inv_heat_number",
    "inventory_grade": "inv_grade",
    "date": "inv_date",
    "posting_date": "inv_posting_date",
    "location_code": "inv_location_code",
    "quantity": "inv_quantity",
    "unit_of_measure_code": "inv_unit_of_measure_code",
    "document_no": "inv_document_no",
    "wsi_variant_code": "inv_wsi_variant_code",
    "dimensions": "inv_dimensions",
    "plate_dimension": "inv_dimensions",
    "internal_bin": "inv_internal_bin",
    "cost_amount_actual": "inv_cost_amount_actual",
    "description_2": "inv_description_2",
    "origin_code": "inv_origin_code",
    "picked": "inv_picked",
    "cutting_plan_no": "inv_cutting_plan_no",
    "image_path": "inv_image_path",
    "entry_type": "inv_entry_type",
    "document_type": "inv_document_type",
    "drawing": "inv_drawing",
    "yield_value": "inv_yield_value",
    "revision": "inv_revision",
    "laser_quality": "inv_laser_quality",
    "unitcost_cwt": "inv_unitcost_cwt",
    "piece_number": "inv_piece_no",
    "variant_code": "inv_variant_code",
    "description": "inv_description",
    "return_reason_code": "inv_return_reason_code",
    "serial_no": "inv_serial_no",
    "package_no": "inv_package_no",
    "invoiced_quantity": "inv_invoiced_quantity",
    "inventory_by_location": "inv_inventory_by_location",
    "inventory": "inv_inventory",
    "expiration_date": "inv_expiration_date",
    "remaining_quantity": "inv_remaining_quantity",
    "shipped_qty_not_returned": "inv_shipped_qty_not_returned",
    "reserved_quantity": "inv_reserved_quantity",
    "qty_per_unit_of_measure": "inv_qty_per_unit_of_measure",
    "sales_amount_expected": "inv_sales_amount_expected",
    "sales_amount_actual": "inv_sales_amount_actual",
    "cost_amount_expected": "inv_cost_amount_expected",
    "cost_amount_non_invtbl": "inv_cost_amount_non_invtbl",
    "item_description": "inv_item_description",
    "cost_amount_expected_acy": "inv_cost_amount_expected_acy",
    "cost_amount_actual_acy": "inv_cost_amount_actual_acy",
    "completely_invoiced": "inv_completely_invoiced",
    "cost_amount_non_invtbl_acy": "inv_cost_amount_non_invtbl_acy",
    "assemble_to_order": "inv_assemble_to_order",
    "drop_shipment": "inv_drop_shipment",
    "open": "inv_open_flag",
    "open_flag": "inv_open_flag",
    "order_type": "inv_order_type",
    "order_no": "inv_order_no",
    "order_line_no": "inv_order_line_no",
    "prod_order_comp_line_no": "inv_prod_order_comp_line_no",
    "entry_no": "inv_entry_no",
    "project_no": "inv_project_no",
    "project_task_no": "inv_project_task_no",
    "source_type": "inv_source_type",
    "source_no": "inv_source_no",
    "source_description": "inv_source_description",
    "source_order_no": "inv_source_order_no",
    "weight": "inv_weight",
    "c": "mtr_c",
    "mn": "mtr_mn",
    "si": "mtr_si",
    "p": "mtr_p",
    "s": "mtr_s",
    "cu": "mtr_cu",
    "ni": "mtr_ni",
    "cr": "mtr_cr",
    "mo": "mtr_mo",
    "n": "mtr_n",
    "b": "mtr_b",
    "v": "mtr_v",
    "nb": "mtr_nb",
    "ti": "mtr_ti",
    "al": "mtr_al",
    "ca": "mtr_ca",
    "zr": "mtr_zr",
    "zn": "mtr_zn",
    "sn": "mtr_sn",
    "ce": "mtr_ce",
    "yield_strength": "mtr_yield_strength",
    "tensile_strength": "mtr_tensile_strength",
    "elongation": "mtr_elongation",
    "reduction_area": "mtr_reduction_area",
    "hardness": "mtr_hardness",
    "thickness": "mtr_thickness",
    "impact_charpy": "mtr_impact_average",
    "plate_dimension": "inv_dimensions",
    "direction": "mtr_direction",
    "impact_test_temp": "mtr_impact_test_temp",
    "impact_coupon_size": "mtr_impact_coupon_size",
    "impact_specimen_1": "mtr_impact_specimen_1",
    "impact_specimen_2": "mtr_impact_specimen_2",
    "impact_specimen_3": "mtr_impact_specimen_3",
    "impact_average": "mtr_impact_average",
}

_FIELD_ALIASES = {
    # heat / batch / grade / manufacturer
    "heat": "heat_number",
    "heatno": "heat_number",
    "heat_no": "heat_number",
    "heatnumber": "heat_number",
    "batch": "batch_number",
    "batchno": "batch_number",
    "batch_no": "batch_number",
    "batchnumber": "batch_number",
    "mat": "grade",
    "material": "grade",
    "material_grade": "grade",
    "materialgrade": "grade",
    "spec": "grade",
    "specification": "grade",
    "mfg": "manufacturer",
    "mill": "manufacturer",
    "supplier": "manufacturer",
    "cert": "certificate_number",
    "certno": "certificate_number",
    "cert_no": "certificate_number",
    "certnumber": "certificate_number",
    "certificate": "certificate_number",
    "certdate": "certificate_date",
    "cert_date": "certificate_date",
    "certificate_date": "certificate_date",
    # origin
    "melt_country": "country_of_melt",
    "melt": "country_of_melt",
    "com": "country_of_manufacture",
    "country_of_manufacture": "country_of_manufacture",
    # inventory
    "lot": "lot_number",
    "lotno": "lot_number",
    "lot_no": "lot_number",
    "item": "item_no",
    "itemno": "item_no",
    "item_no": "item_no",
    "slab": "slab_number",
    "slabno": "slab_number",
    "slab_no": "slab_number",
    "inv_heat": "inventory_heat_number",
    "inventory_heat": "inventory_heat_number",
    "inv_grade": "inventory_grade",
    "inventory_grade": "inventory_grade",
    "posting": "posting_date",
    "postingdate": "posting_date",
    "posting_date": "posting_date",
    "location": "location_code",
    "locationcode": "location_code",
    "location_code": "location_code",
    "qty": "quantity",
    "quantity": "quantity",
    "uom": "unit_of_measure_code",
    "unit": "unit_of_measure_code",
    "unit_of_measure_code": "unit_of_measure_code",
    "doc": "document_no",
    "document": "document_no",
    "document_no": "document_no",
    "variant": "variant_code",
    "variant_code": "variant_code",
    "description": "description",
    "item_description": "item_description",
    "source": "source_description",
    "source_no": "source_no",
    "source_order_no": "source_order_no",
    "weight": "weight",
    "weightkg": "weight",
    "weight_kg": "weight",
    # chemistry
    "carbon": "c",
    "c%": "c",
    "c_element": "c",
    "manganese": "mn",
    "mn%": "mn",
    "mn_element": "mn",
    "silicon": "si",
    "si%": "si",
    "si_element": "si",
    "phosphorus": "p",
    "p%": "p",
    "p_element": "p",
    "sulfur": "s",
    "s%": "s",
    "s_element": "s",
    "copper": "cu",
    "cu%": "cu",
    "cu_element": "cu",
    "nickel": "ni",
    "ni%": "ni",
    "ni_element": "ni",
    "chromium": "cr",
    "cr%": "cr",
    "cr_element": "cr",
    "molybdenum": "mo",
    "mo%": "mo",
    "mo_element": "mo",
    "nitrogen": "n",
    "n%": "n",
    "n_element": "n",
    "boron": "b",
    "b%": "b",
    "b_element": "b",
    "vanadium": "v",
    "v%": "v",
    "v_element": "v",
    "niobium": "nb",
    "nb%": "nb",
    "nb_element": "nb",
    "titanium": "ti",
    "ti%": "ti",
    "ti_element": "ti",
    "aluminum": "al",
    "aluminium": "al",
    "al%": "al",
    "al_element": "al",
    "calcium": "ca",
    "ca%": "ca",
    "ca_element": "ca",
    "zirconium": "zr",
    "zr%": "zr",
    "zr_element": "zr",
    "zinc": "zn",
    "zn%": "zn",
    "zn_element": "zn",
    "tin": "sn",
    "sn%": "sn",
    "sn_element": "sn",
    "chemical equivalency": "ce",
    "chemical equivalence": "ce",
    "carbon equivalent": "ce",
    # mechanical
    "ys": "yield_strength",
    "yield": "yield_strength",
    "yieldstrength": "yield_strength",
    "yield_strength": "yield_strength",
    "ys_ksi": "yield_strength",
    "uts": "tensile_strength",
    "tensile": "tensile_strength",
    "tensilestrength": "tensile_strength",
    "tensile_strength": "tensile_strength",
    "elong": "elongation",
    "elongation": "elongation",
    "ra": "reduction_area",
    "reductionarea": "reduction_area",
    "reduction_area": "reduction_area",
    "hard": "hardness",
    "hardness": "hardness",
    "hrb": "hardness",
    "hrc": "hardness",
    "thk": "thickness",
    "thickness": "thickness",
    "impact_charpy": "impact_average",
    "direction": "direction",
    "long": "direction",
    "longitudinal": "direction",
    "l": "direction",
    "trans": "direction",
    "transverse": "direction",
    "t": "direction",
    # impact
    "impact": "impact_average",
    "charpy": "impact_average",
    "impact_average": "impact_average",
    "impactavg": "impact_average",
    "impact_temp": "impact_test_temp",
    "impact_test_temp": "impact_test_temp",
    "impact_cpn_size": "impact_coupon_size",
    "impact_coupon_size": "impact_coupon_size",
    "impact1": "impact_specimen_1",
    "impact_1": "impact_specimen_1",
    "impact2": "impact_specimen_2",
    "impact_2": "impact_specimen_2",
    "impact3": "impact_specimen_3",
    "impact_3": "impact_specimen_3",
}

_MTR_FIELD_MAP = {
    "heat_number": "heat_number",
    "batch_number": "batch_number",
    "grade": "grade",
    "manufacturer": "manufacturer",
    "certificate_number": "certificate_number",
    "certificate_date": "certificate_date",
    "country_of_melt": "country_of_melt",
    "country_of_manufacture": "country_of_manufacture",
    "piece_no": "piece_no",
    "c": "c_element",
    "mn": "mn_element",
    "si": "si_element",
    "p": "p_element",
    "s": "s_element",
    "b": "b_element",
    "v": "v_element",
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
    "ce": "ce",
    "yield_strength": "yield_strength",
    "tensile_strength": "tensile_strength",
    "elongation": "elongation",
    "reduction_area": "reduction_area",
    "hardness": "hardness",
    "thickness": "thickness",
    "impact_charpy": "impact_charpy",
    "direction": "direction",
    "impact_test_temp": "impact_test_temp",
    "impact_coupon_size": "impact_coupon_size",
    "impact_specimen_1": "impact_specimen_1",
    "impact_specimen_2": "impact_specimen_2",
    "impact_specimen_3": "impact_specimen_3",
    "impact_average": "impact_average",
}

_NUMERIC_FIELDS = {
    "mtr_c",
    "mtr_mn",
    "mtr_si",
    "mtr_p",
    "mtr_s",
    "mtr_b",
    "mtr_v",
    "mtr_nb",
    "mtr_ti",
    "mtr_al",
    "mtr_ca",
    "mtr_zr",
    "mtr_zn",
    "mtr_sn",
    "mtr_cu",
    "mtr_ni",
    "mtr_cr",
    "mtr_mo",
    "mtr_n",
    "mtr_ce",
    "mtr_piece_no",
    "inv_quantity",
    "inv_cost_amount_actual",
    "inv_yield_value",
    "inv_invoiced_quantity",
    "inv_inventory_by_location",
    "inv_inventory",
    "inv_remaining_quantity",
    "inv_shipped_qty_not_returned",
    "inv_reserved_quantity",
    "inv_qty_per_unit_of_measure",
    "inv_sales_amount_expected",
    "inv_sales_amount_actual",
    "inv_cost_amount_expected",
    "inv_cost_amount_non_invtbl",
    "inv_cost_amount_expected_acy",
    "inv_cost_amount_actual_acy",
    "inv_cost_amount_non_invtbl_acy",
    "inv_unitcost_cwt",
    "inv_weight",
    "inv_order_line_no",
    "inv_prod_order_comp_line_no",
    "inv_entry_no",
    "mtr_yield_strength",
    "mtr_tensile_strength",
    "mtr_elongation",
    "mtr_reduction_area",
    "mtr_hardness",
    "mtr_piece_no",
    "mtr_thickness",
    "mtr_impact_charpy",
    "mtr_impact_test_temp",
    "mtr_impact_specimen_1",
    "mtr_impact_specimen_2",
    "mtr_impact_specimen_3",
    "mtr_impact_average",
}

_MTR_NUMERIC_FIELDS = {
    "c_element",
    "mn_element",
    "si_element",
    "p_element",
    "s_element",
    "b_element",
    "v_element",
    "nb_element",
    "ti_element",
    "al_element",
    "ca_element",
    "zr_element",
    "zn_element",
    "sn_element",
    "cu_element",
    "ni_element",
    "cr_element",
    "mo_element",
    "n_element",
    "ce",
    "piece_no",
    "yield_strength",
    "tensile_strength",
    "elongation",
    "reduction_area",
    "hardness",
    "thickness",
    "impact_charpy",
    "impact_test_temp",
    "impact_specimen_1",
    "impact_specimen_2",
    "impact_specimen_3",
    "impact_average",
}

_TEXT_FIELDS = {
    "mtr_heat_number",
    "mtr_batch_number",
    "mtr_grade",
    "mtr_manufacturer",
    "mtr_certificate_number",
    "mtr_country_of_melt",
    "mtr_country_of_manufacture",
    "inv_lot_number",
    "inv_item_no",
    "inv_slab_number",
    "inv_heat_number",
    "inv_grade",
    "inv_location_code",
    "inv_unit_of_measure_code",
    "inv_document_no",
    "inv_wsi_variant_code",
    "inv_dimensions",
    "inv_internal_bin",
    "inv_description_2",
    "inv_origin_code",
    "inv_picked",
    "inv_cutting_plan_no",
    "inv_image_path",
    "inv_entry_type",
    "inv_document_type",
    "inv_drawing",
    "inv_revision",
    "inv_laser_quality",
    "inv_piece_no",
    "inv_variant_code",
    "inv_description",
    "inv_return_reason_code",
    "inv_serial_no",
    "inv_package_no",
    "inv_completely_invoiced",
    "inv_assemble_to_order",
    "inv_drop_shipment",
    "inv_open_flag",
    "inv_order_type",
    "inv_order_no",
    "inv_project_no",
    "inv_project_task_no",
    "inv_source_type",
    "inv_source_no",
    "inv_source_description",
    "inv_source_order_no",
    "inv_country_of_melt",
    "inv_country_of_manufacture",
}

_MTR_TEXT_FIELDS = {
    "heat_number",
    "batch_number",
    "grade",
    "manufacturer",
    "certificate_number",
    "country_of_melt",
    "country_of_manufacture",
    "direction",
    "impact_coupon_size",
}

_TEXT_SEARCH_FIELDS = [
    "mtr_batch_number",
    "mtr_heat_number",
    "mtr_grade",
    "mtr_manufacturer",
    "mtr_certificate_number",
    "inv_lot_number",
    "inv_item_no",
    "inv_description",
    "inv_heat_number",
    "inv_slab_number",
    "inv_grade",
    "inv_location_code",
    "inv_unit_of_measure_code",
    "inv_document_no",
    "inv_wsi_variant_code",
    "inv_dimensions",
    "inv_internal_bin",
    "inv_description_2",
    "inv_origin_code",
    "inv_picked",
    "inv_cutting_plan_no",
    "inv_image_path",
    "inv_entry_type",
    "inv_document_type",
    "inv_drawing",
    "inv_revision",
    "inv_laser_quality",
    "inv_piece_no",
    "inv_variant_code",
    "inv_return_reason_code",
    "inv_serial_no",
    "inv_package_no",
    "inv_completely_invoiced",
    "inv_assemble_to_order",
    "inv_drop_shipment",
    "inv_open_flag",
    "inv_order_type",
    "inv_order_no",
    "inv_project_no",
    "inv_project_task_no",
    "inv_source_type",
    "inv_source_no",
    "inv_source_description",
    "inv_source_order_no",
    "inv_country_of_melt",
    "inv_country_of_manufacture",
]

_MTR_TEXT_SEARCH_FIELDS = [
    "batch_number",
    "heat_number",
    "grade",
    "manufacturer",
    "certificate_number",
    "country_of_melt",
    "country_of_manufacture",
    "direction",
    "impact_coupon_size",
]

_ALLOWED_OPS = {"=", "!=", ">=", "<=", ">", "<", "ilike", "not ilike"}

_SEARCH_SCHEMA_GUIDE = """
Data model guide:

MTR record example:
{
  "batch_number": "0005T6-03",
  "heat_number": "0005T6-03",
  "piece_no": "1",
  "grade": "A36",
  "manufacturer": "XYZ Steel",
  "certificate_number": "MT12345",
  "certificate_date": "2024-01-15",
  "country_of_melt": "USA",
  "country_of_manufacture": "USA",
  "c_element": 0.17,
  "mn_element": 1.02,
  "si_element": 0.22,
  "p_element": 0.01,
  "s_element": 0.005,
  "b_element": 0.0,
  "v_element": 0.0,
  "nb_element": 0.0,
  "ti_element": 0.0,
  "al_element": 0.02,
  "ca_element": 0.0,
  "zr_element": 0.0,
  "zn_element": 0.0,
  "sn_element": 0.0,
  "cu_element": 0.03,
  "ni_element": 0.02,
  "cr_element": 0.05,
  "mo_element": 0.01,
  "n_element": 0.004,
  "ce": 0.33,
  "yield_strength": 360,
  "tensile_strength": 520,
  "elongation": 22,
  "reduction_area": 45,
  "hardness": 150,
  "thickness": 12.7,
  "impact_charpy": 0,
  "impact_test_temp": -20,
  "impact_coupon_size": "10x10",
  "impact_specimen_1": 18,
  "impact_specimen_2": 20,
  "impact_specimen_3": 19,
  "impact_average": 19
}

Inventory record example:
{
  "lot_number": "LOT-1001",
  "heat_number": "0005T6-03",
  "slab_number": "SL-7788",
  "item_no": "I-200",
  "grade": "A36",
  "dimensions": "1/4 x 48 x 120",
  "weight": 1000,
  "posting_date": "2024-02-10",
  "location_code": "MAIN",
  "unit_of_measure_code": "LB",
  "description": "Plate",
  "item_description": "Hot rolled plate",
  "serial_no": "S123",
  "package_no": "P456",
  "source_description": "Received from mill",
  "source_order_no": "SO-9001",
  "country_of_melt": "USA",
  "country_of_manufacture": "USA"
}

Join report example:
{
  "inv_lot_number": "LOT-1001",
  "inv_heat_number": "0005T6-03",
  "mtr_batch_number": "0005T6-03",
  "mtr_grade": "A36",
  "mtr_manufacturer": "XYZ Steel",
  "mtr_c": 0.17,
  "mtr_mn": 1.02,
  "mtr_yield_strength": 360,
  "mtr_tensile_strength": 520
}
""".strip()


def _extract_json(text):
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except Exception:
        return None


def _coerce_value(field, value, numeric_fields=None):
    if value is None:
        return None
    numeric_fields = numeric_fields or _NUMERIC_FIELDS
    if field in numeric_fields:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    return value


def _or_domain(clauses):
    clauses = [clause for clause in clauses if clause]
    if not clauses:
        return []
    if len(clauses) == 1:
        return [clauses[0]]
    return ["|"] * (len(clauses) - 1) + clauses


def _build_filters_domain(filters):
    domain = []
    for entry in filters or []:
        field_key = (entry.get("field") or "").strip().lower()
        field_key = _FIELD_ALIASES.get(field_key, field_key)
        op = (entry.get("op") or "=").strip()
        value = entry.get("value")
        field = _FIELD_MAP.get(field_key)
        if not field or op not in _ALLOWED_OPS:
            continue
        if field == "mtr_direction" and isinstance(value, str):
            variants = _direction_query_variants(value)
            if variants:
                domain.extend(_or_domain([(field, "ilike", variant) for variant in variants]))
                continue
        numeric_value = _coerce_value(field, value, _NUMERIC_FIELDS)
        if op == "=" and field in _NUMERIC_FIELDS and numeric_value == 0:
            domain.extend(["|", (field, "=", 0), (field, "=", False)])
            continue
        value = numeric_value
        if value in (None, ""):
            continue
        if op == "=" and field in _TEXT_FIELDS and isinstance(value, str):
            op = "ilike"
        elif op == "!=" and field in _TEXT_FIELDS and isinstance(value, str):
            op = "not ilike"
        domain.append((field, op, value))
    return domain


def _build_text_domain(text_query):
    if not text_query:
        return []
    clauses = [(field, "ilike", text_query) for field in _TEXT_SEARCH_FIELDS]
    return _or_domain(clauses)


def _build_mtr_filters_domain(filters):
    domain = []
    for entry in filters or []:
        field_key = (entry.get("field") or "").strip().lower()
        field_key = _FIELD_ALIASES.get(field_key, field_key)
        op = (entry.get("op") or "=").strip()
        value = entry.get("value")
        field = _MTR_FIELD_MAP.get(field_key)
        if not field or op not in _ALLOWED_OPS:
            continue
        if field == "direction" and isinstance(value, str):
            variants = _direction_query_variants(value)
            if variants:
                domain.extend(_or_domain([(field, "ilike", variant) for variant in variants]))
                continue
        numeric_value = _coerce_value(field, value, _MTR_NUMERIC_FIELDS)
        if op == "=" and field in _MTR_NUMERIC_FIELDS and numeric_value == 0:
            domain.extend(["|", (field, "=", 0), (field, "=", False)])
            continue
        value = numeric_value
        if value in (None, ""):
            continue
        if op == "=" and field in _MTR_TEXT_FIELDS and isinstance(value, str):
            op = "ilike"
        elif op == "!=" and field in _MTR_TEXT_FIELDS and isinstance(value, str):
            op = "not ilike"
        domain.append((field, op, value))
    return domain


def _build_mtr_text_domain(text_query):
    if not text_query:
        return []
    clauses = [(field, "ilike", text_query) for field in _MTR_TEXT_SEARCH_FIELDS]
    return _or_domain(clauses)


def _extract_dimension_value(message):
    text = " ".join((message or "").split())
    if not text:
        return ""
    m = re.search(r"(\d+(?:\.\d+)?\s*\"?\s*x\s*\d+(?:\.\d+)?\s*\"?\s*x\s*\d+(?:\.\d+)?\s*\"?)", text, re.IGNORECASE)
    if m:
        return m.group(1).replace("  ", " ").strip()
    return ""


def _normalize_dimension_value(value):
    text = " ".join((value or "").split())
    if not text:
        return ""
    text = text.replace('"', "")
    text = re.sub(r"\s*x\s*", " x ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _normalize_direction_value(value):
    text = " ".join((value or "").split()).strip()
    if not text:
        return ""
    lowered = text.lower()
    if lowered in {"l", "long", "longitudinal"}:
        return "Longitudinal"
    if lowered in {"t", "trans", "transverse"}:
        return "Transverse"
    return text.title() if len(text) <= 3 else text


def _direction_query_variants(value):
    text = _normalize_direction_value(value)
    if not text:
        return []
    lowered = text.lower()
    variants = [text]
    if lowered.startswith("long"):
        variants.extend(["L", "l", "Long", "Longitudinal", "longitudinal"])
    elif lowered.startswith("trans"):
        variants.extend(["T", "t", "Trans", "Transverse", "transverse"])
    else:
        variants.extend([text.upper(), text.lower()])
    unique = []
    for item in variants:
        if item and item not in unique:
            unique.append(item)
    return unique


def _dimension_query_variants(value):
    raw = " ".join((value or "").split())
    text = _normalize_dimension_value(value)
    if not raw and not text:
        return []
    compact = text.replace(" ", "")
    spaced = re.sub(r"\s*x\s*", " x ", text, flags=re.IGNORECASE)
    variants = []
    for candidate in (raw, text):
        if candidate and candidate not in variants:
            variants.append(candidate)
    for variant in (compact, spaced, spaced.replace(" x ", "x")):
        if variant and variant not in variants:
            variants.append(variant)
    return variants


def _dimension_component_variants(value):
    text = _normalize_dimension_value(value)
    if not text:
        return []
    parts = []
    for raw_part in re.split(r"\s*x\s*", text, flags=re.IGNORECASE):
        part = raw_part.strip()
        if not part:
            continue
        trimmed = part
        if re.fullmatch(r"\d+\.\d+", part):
            trimmed = part.rstrip("0").rstrip(".")
        if trimmed not in parts:
            parts.append(trimmed)
    return parts


def _expand_identifier_filter_variants(filters):
    base = [dict(entry) for entry in (filters or [])]
    variants = [base]
    identifier_fields = {"heat_number", "batch_number"}
    for index, entry in enumerate(base):
        field = (entry.get("field") or "").strip().lower()
        if field not in identifier_fields:
            continue
        alternate = "batch_number" if field == "heat_number" else "heat_number"
        if alternate == field:
            continue

        swapped = [dict(item) for item in base]
        swapped[index]["field"] = alternate
        variants.append(swapped)

        relaxed_original = [dict(item) for item in base]
        if (relaxed_original[index].get("op") or "=").strip() == "=":
            relaxed_original[index]["op"] = "ilike"
        variants.append(relaxed_original)

        relaxed_swapped = [dict(item) for item in swapped]
        if (relaxed_swapped[index].get("op") or "=").strip() == "=":
            relaxed_swapped[index]["op"] = "ilike"
        variants.append(relaxed_swapped)
    return variants


def _extract_batch_identifier(message):
    text = " ".join((message or "").split())
    if not text:
        return ""

    has_batch_context = re.search(r"\b(?:batch(?:\s*(?:no|number|#))?|bn|heat(?:\s*(?:no|number|#))?)\b", text, re.IGNORECASE)
    has_field_context = re.search(
        r"\b(?:grade|manufacturer|certificate|carbon|c%|manganese|mn%|silicon|si%|phosphorus|p%|sulfur|s%|copper|cu%|nickel|ni%|chromium|cr%|molybdenum|mo%|nitrogen|n%|boron|b%|vanadium|v%|niobium|nb%|titanium|ti%|aluminum|aluminium|al%|calcium|ca%|zirconium|zr%|zinc|zn%|tin|sn%|yield|tensile|elongation|reduction|hardness|thickness|impact|lot|item|slab|weight|quantity|location|posting|document|description|variant|serial|package|source|order|project|entry|uom|unit|bin)\b",
        text,
        re.IGNORECASE,
    )

    patterns = [
        r"\b(?:batch(?:\s*(?:no|number|#))?|bn)\b\s*[:#=\-]?\s*([A-Za-z0-9][A-Za-z0-9._/\-]*)",
        r"\b(?:batch(?:\s*(?:no|number|#))?|bn)\b\s+([A-Za-z0-9][A-Za-z0-9._/\-]*)",
        r"\b(?:heat(?:\s*(?:no|number|#))?)\b\s*[:#=\-]?\s*([A-Za-z0-9][A-Za-z0-9._/\-]*)",
        r"\b(?:heat(?:\s*(?:no|number|#))?)\b\s+([A-Za-z0-9][A-Za-z0-9._/\-]*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip(".,;:()[]{}")

    # Fall back to a standalone batch-like token when the user just types the id
    # or mixes it into a short sentence, e.g. "find DA2291".
    if has_field_context and not has_batch_context:
        return ""

    stop_words = {
        "find", "show", "get", "lookup", "search", "open", "view",
        "the", "a", "an", "for", "by", "batch", "number", "no", "id",
        "please", "mtr", "report", "record", "records",
    }
    tokens = [t.strip(".,;:()[]{}") for t in re.split(r"\s+", text) if t.strip()]
    candidates = []
    for token in tokens:
        low = token.lower()
        if low in stop_words:
            continue
        if re.fullmatch(r"\d+(?:[.,]\d+)?", token):
            continue
        if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/\-]*", token) and re.search(r"\d", token):
            candidates.append(token)

    if len(candidates) == 1:
        return candidates[0]

    # If the message mentions batch and contains multiple tokens, prefer the token
    # closest to the batch keyword.
    if candidates and re.search(r"\bbatch\b", text, re.IGNORECASE):
        batch_pos = re.search(r"\bbatch\b", text, re.IGNORECASE).start()
        best = None
        best_dist = None
        for token in candidates:
            m = re.search(re.escape(token), text, re.IGNORECASE)
            if not m:
                continue
            dist = abs(m.start() - batch_pos)
            if best_dist is None or dist < best_dist:
                best = token
                best_dist = dist
        if best:
            return best
    return ""


def _search_batch_first(env, batch_identifier, message=None, limit=20):
    identifier = (batch_identifier or "").strip()
    if not identifier:
        return None

    report = env["mtr.inventory.join.report"]
    fields = [
        "id",
        "join_status",
        "inv_lot_number",
        "inv_item_no",
        "inv_description",
        "inv_heat_number",
        "inv_slab_number",
        "inv_posting_date",
        "mtr_id",
        "mtr_heat_number",
        "mtr_batch_number",
        "mtr_piece_no",
        "mtr_grade",
        "mtr_manufacturer",
        "mtr_certificate_number",
        "mtr_certificate_date",
        "mtr_c",
        "mtr_mn",
        "mtr_ce",
        "mtr_yield_strength",
        "mtr_tensile_strength",
        "mtr_thickness",
    ]

    join_domain = _or_domain([
        ("mtr_batch_number", "=", identifier),
        ("mtr_batch_number", "ilike", identifier),
        ("mtr_heat_number", "=", identifier),
        ("mtr_heat_number", "ilike", identifier),
    ])
    results = report.search_read(_MATCHED_ONLY_DOMAIN + join_domain, fields=fields, limit=limit)
    for row in results:
        row["join_id"] = row.get("id")

    if results:
        return {
            "answer": _format_direct_lookup_answer(identifier, results, "Join Report", message=message),
            "results": results,
            "filters": [{"field": "batch_number", "op": "=", "value": identifier}],
            "text_query": "",
        }

    mtr_domain = _or_domain([
        ("batch_number", "=", identifier),
        ("batch_number", "ilike", identifier),
        ("heat_number", "=", identifier),
        ("heat_number", "ilike", identifier),
    ])
    mtr_fields = [
        "id",
        "heat_number",
        "batch_number",
        "piece_no",
        "grade",
        "manufacturer",
        "certificate_number",
        "certificate_date",
        "country_of_melt",
        "country_of_manufacture",
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
    ]
    mtr_results = env["mtr.data"].search_read(mtr_domain, fields=mtr_fields, limit=limit)
    if not mtr_results:
        return {
            "answer": _(
                "I could not find heat or batch %(identifier)s. "
                "What can we do next? We can search by batch number, heat number, grade, manufacturer, or certificate number."
            ) % {"identifier": identifier},
            "results": [],
            "filters": [{"field": "batch_number", "op": "=", "value": identifier}],
            "text_query": "",
        }

    results = []
    for row in mtr_results:
        results.append({
            "join_id": None,
            "join_status": "MTR only",
            "mtr_id": row.get("id"),
            "mtr_batch_number": row.get("batch_number"),
            "mtr_piece_no": row.get("piece_no") or 0,
            "mtr_heat_number": row.get("heat_number"),
            "mtr_grade": row.get("grade"),
            "mtr_manufacturer": row.get("manufacturer"),
            "mtr_certificate_number": row.get("certificate_number"),
            "mtr_certificate_date": row.get("certificate_date"),
            "mtr_c": row.get("c_element"),
            "mtr_mn": row.get("mn_element"),
            "mtr_ce": row.get("ce"),
            "mtr_si": row.get("si_element"),
            "mtr_p": row.get("p_element"),
            "mtr_s": row.get("s_element"),
            "mtr_cu": row.get("cu_element"),
            "mtr_ni": row.get("ni_element"),
            "mtr_cr": row.get("cr_element"),
            "mtr_mo": row.get("mo_element"),
            "mtr_n": row.get("n_element"),
            "mtr_yield_strength": row.get("yield_strength"),
            "mtr_tensile_strength": row.get("tensile_strength"),
            "mtr_elongation": row.get("elongation"),
            "mtr_reduction_area": row.get("reduction_area"),
            "mtr_hardness": row.get("hardness"),
            "mtr_thickness": row.get("thickness"),
            "mtr_impact_test_temp": row.get("impact_test_temp"),
            "mtr_impact_coupon_size": row.get("impact_coupon_size"),
            "mtr_impact_specimen_1": row.get("impact_specimen_1"),
            "mtr_impact_specimen_2": row.get("impact_specimen_2"),
            "mtr_impact_specimen_3": row.get("impact_specimen_3"),
            "mtr_impact_average": row.get("impact_average"),
            "mtr_country_of_melt": row.get("country_of_melt"),
            "mtr_country_of_manufacture": row.get("country_of_manufacture"),
        })
    return {
        "answer": _format_direct_lookup_answer(identifier, results, "MTR Records", message=message),
        "results": results,
        "filters": [{"field": "batch_number", "op": "=", "value": identifier}],
        "text_query": "",
    }


def _detect_lookup_topic(message):
    text = (message or "").lower()
    if re.search(r"\bgrade\b", text):
        return "grade"
    if re.search(r"\bmanufacturer\b|\bmfg\b|\bmill\b", text):
        return "manufacturer"
    if re.fullmatch(r"\s*mt[0-9a-z]+\s*", text):
        return "certificate"
    if re.search(r"\bcertificate\b|\bcert\b", text):
        return "certificate"
    if re.search(r"\bchem(?:istry)?\b|\bchemical\b", text):
        return "chemistry"
    if re.search(r"\bmech(?:anical)?\b", text):
        return "mechanical"
    if re.search(r"\bimpact\b", text):
        return "impact"
    return "general"


def _pick_first_nonempty(rows, fields):
    for row in rows or []:
        for field in fields:
            value = row.get(field)
            if value not in (None, ""):
                return value
    return ""


def _unique_nonempty_values(rows, fields):
    values = []
    seen = set()
    for row in rows or []:
        for field in fields:
            value = row.get(field)
            if value in (None, ""):
                continue
            text = str(value).strip()
            if not text or text in seen:
                continue
            seen.add(text)
            values.append(text)
    return values


def _humanize_field_name(field_key):
    text = (field_key or "").strip().replace("_", " ")
    return text[:1].upper() + text[1:] if text else ""


def _format_filter_value(value):
    if isinstance(value, float):
        text = ("%.5f" % value).rstrip("0").rstrip(".")
        return text if text else "0"
    return str(value)


def _format_search_criteria(filters=None, text_query=""):
    parts = []
    for entry in filters or []:
        field = (entry.get("field") or "").strip()
        op = (entry.get("op") or "=").strip()
        value = entry.get("value")
        if not field:
            continue
        field_label = _humanize_field_name(field)
        if op == "=":
            parts.append("%s = %s" % (field_label, _format_filter_value(value)))
        else:
            parts.append("%s %s %s" % (field_label, op, _format_filter_value(value)))
    if parts:
        return ", ".join(parts)
    if text_query:
        return '"%s"' % text_query
    return ""


def _format_no_results_answer(source_label, filters=None, text_query=""):
    criteria = _format_search_criteria(filters, text_query)
    if criteria:
        if (source_label or "").strip().lower().endswith("records"):
            return _("No %(source)s found for %(criteria)s.") % {
                "source": source_label,
                "criteria": criteria,
            }
        return _("No %(source)s records found for %(criteria)s.") % {
            "source": source_label,
            "criteria": criteria,
        }
    return _("No %(source)s records found.") % {"source": source_label}


def _format_direct_lookup_answer(identifier, results, source_label, message=None):
    topic = _detect_lookup_topic(message or identifier)
    identifier_text = identifier or _("that heat")

    if topic == "grade":
        grades = _unique_nonempty_values(results, ["mtr_grade"])
        if len(grades) == 1:
            return _("Heat %(identifier)s has grade %(grade)s.") % {
                "identifier": identifier_text,
                "grade": grades[0],
            }
        if grades:
            return _("I found %(count)s record(s) for heat %(identifier)s in %(source)s. Grades: %(grades)s.") % {
                "count": len(results),
                "identifier": identifier_text,
                "source": source_label,
                "grades": ", ".join(grades),
            }

    if topic == "manufacturer":
        manufacturer = _pick_first_nonempty(results, ["mtr_manufacturer"])
        if manufacturer:
            return _("Heat %(identifier)s was manufactured by %(manufacturer)s.") % {
                "identifier": identifier_text,
                "manufacturer": manufacturer,
            }

    if topic == "certificate":
        certificate = _pick_first_nonempty(results, ["mtr_certificate_number"])
        if certificate:
            return _("Heat %(identifier)s has certificate number %(certificate)s.") % {
                "identifier": identifier_text,
                "certificate": certificate,
            }

    return _("Fetched %(count)s result(s) from %(source)s for %(identifier)s.") % {
        "count": len(results),
        "source": source_label,
        "identifier": identifier_text,
    }


def _format_exact_field_answer(results, field_key):
    field_key = (field_key or "").strip().lower()
    if not field_key:
        return ""
    spec = _FIELD_RESPONSE_MAP.get(field_key)
    if spec:
        label, candidates = spec
    else:
        label = _humanize_field_name(field_key)
        candidates = [field_key]

    values = []
    seen = set()
    for row in results or []:
        value = ""
        for candidate in candidates:
            value = row.get(candidate)
            if value not in (None, ""):
                break
        if value in (None, "") and field_key in {
            "piece_no",
            "c",
            "mn",
            "si",
            "p",
            "s",
            "b",
            "v",
            "nb",
            "ti",
            "al",
            "ca",
            "zr",
            "zn",
            "sn",
            "cu",
            "ni",
            "cr",
            "mo",
            "n",
            "ce",
            "yield_strength",
            "tensile_strength",
            "elongation",
            "reduction_area",
            "hardness",
            "thickness",
            "impact_charpy",
            "impact_test_temp",
            "impact_coupon_size",
            "impact_specimen_1",
            "impact_specimen_2",
            "impact_specimen_3",
            "impact_average",
        }:
            value = 0
        if value in (None, ""):
            continue
        text = _format_filter_value(value) if isinstance(value, float) else str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        values.append(text)

    if not values:
        return ""
    if len(values) == 1:
        return "%s: %s" % (label, values[0])
    return "%s: %s" % (label, "; ".join(values))


_CHEMISTRY_FIELD_KEYS = [
    "c",
    "mn",
    "si",
    "p",
    "s",
    "b",
    "v",
    "nb",
    "ti",
    "al",
    "ca",
    "zr",
    "zn",
    "sn",
    "cu",
    "ni",
    "cr",
    "mo",
    "n",
    "ce",
]


def _format_chemistry_block_answer(results):
    lines = []
    for field_key in _CHEMISTRY_FIELD_KEYS:
        line = _format_exact_field_answer(results, field_key)
        if line:
            lines.append(line)
    return "\n".join(lines)


_MECHANICAL_FIELD_KEYS = [
    "yield_strength",
    "tensile_strength",
    "elongation",
    "reduction_area",
    "hardness",
    "thickness",
    "plate_dimension",
    "direction",
]


_IMPACT_FIELD_KEYS = [
    "impact_charpy",
    "impact_test_temp",
    "impact_coupon_size",
    "impact_specimen_1",
    "impact_specimen_2",
    "impact_specimen_3",
    "impact_average",
]


_MTR_FIRST_TARGET_FIELDS = {"direction", "uploaded_at", "thickness", "impact_test_temp", "piece_no"}


_PROPERTY_TOPIC_FIELD_KEYS = {
    "chemistry": _CHEMISTRY_FIELD_KEYS,
    "mechanical": _MECHANICAL_FIELD_KEYS,
    "impact": _IMPACT_FIELD_KEYS,
}


_PROPERTY_TOPIC_LABELS = {
    "chemistry": "Chemical Properties",
    "mechanical": "Mechanical Properties",
    "impact": "Impact Values",
}


def _detect_property_topics(message):
    text = (message or "").lower()
    topics = []
    if re.search(r"\bchemical properties?\b|\bchemical composition\b|\bchemistry\b", text):
        topics.append("chemistry")
    if re.search(r"\bmechanical properties?\b|\bmech(?:anical)?\b", text):
        topics.append("mechanical")
    if re.search(r"\bimpact values?\b|\bimpact properties?\b|\bimpact block\b", text):
        topics.append("impact")
    return topics


def _format_property_blocks_answer(results, topics):
    blocks = []
    topics = [topic for topic in (topics or []) if topic in _PROPERTY_TOPIC_FIELD_KEYS]
    if not topics:
        return ""

    many_topics = len(topics) > 1
    for topic in topics:
        block = []
        for field_key in _PROPERTY_TOPIC_FIELD_KEYS[topic]:
            line = _format_exact_field_answer(results, field_key)
            if line:
                block.append(line)
        if not block:
            continue
        text = "\n".join(block)
        if many_topics:
            text = "%s:\n%s" % (_PROPERTY_TOPIC_LABELS[topic], text)
        blocks.append(text)
    return "\n\n".join(blocks)


def _find_matching_spec_for_grade(env, grade_text):
    grade = (grade_text or "").strip()
    if not grade:
        return None
    spec = env["mtr.specification"].search([
        "|",
        ("name", "ilike", grade),
        ("astm_equivalent", "ilike", grade),
    ], limit=1)
    if spec:
        return spec
    return None


def _grade_specificity(value):
    text = (value or "").strip()
    if not text:
        return (-1, -1, "")
    has_spaces = 1 if " " in text else 0
    return (len(text), has_spaces, text.lower())


_FIELD_RESPONSE_MAP = {
    "grade": ("Grade", ["mtr_grade", "inv_grade", "grade"]),
    "manufacturer": ("Manufacturer", ["mtr_manufacturer"]),
    "certificate_number": ("Certificate Number", ["mtr_certificate_number"]),
    "certificate_date": ("Certificate Date", ["mtr_certificate_date"]),
    "batch_number": ("Batch Number", ["mtr_batch_number", "mtr_heat_number", "inv_heat_number", "batch_number", "heat_number"]),
    "heat_number": ("Heat Number", ["mtr_heat_number", "mtr_batch_number", "inv_heat_number", "heat_number", "batch_number"]),
    "piece_no": ("Piece No", ["mtr_piece_no", "inv_piece_no", "piece_no"]),
    "lot_number": ("Lot Number", ["inv_lot_number", "lot_number"]),
    "item_no": ("Item No", ["inv_item_no", "item_no"]),
    "slab_number": ("Slab Number", ["inv_slab_number", "slab_number"]),
    "location_code": ("Location Code", ["inv_location_code", "location_code"]),
    "uploaded_at": ("Uploaded At", ["mtr_uploaded_at", "uploaded_at"]),
    "quantity": ("Quantity", ["inv_quantity", "quantity"]),
    "unit_of_measure_code": ("Unit of Measure Code", ["inv_unit_of_measure_code", "unit_of_measure_code"]),
    "document_no": ("Document No", ["inv_document_no", "document_no"]),
    "document_line_no": ("Document Line No", ["inv_document_line_no", "document_line_no"]),
    "variant_code": ("Variant Code", ["inv_variant_code", "variant_code"]),
    "wsi_variant_code": ("WSI Variant Code", ["inv_wsi_variant_code", "wsi_variant_code"]),
    "description": ("Description", ["inv_description", "description"]),
    "description_2": ("Description 2", ["inv_description_2", "description_2"]),
    "item_description": ("Item Description", ["inv_item_description", "item_description"]),
    "additional_notes": ("Additional Notes", ["inv_additional_notes", "additional_notes"]),
    "source_description": ("Source Description", ["inv_source_description", "source_description"]),
    "source_order_no": ("Source Order No", ["inv_source_order_no", "source_order_no"]),
    "source_no": ("Source No", ["inv_source_no", "source_no"]),
    "source_type": ("Source Type", ["inv_source_type", "source_type"]),
    "serial_no": ("Serial No", ["inv_serial_no", "serial_no"]),
    "package_no": ("Package No", ["inv_package_no", "package_no"]),
    "internal_bin": ("Internal Bin", ["inv_internal_bin", "internal_bin"]),
    "cutting_plan_no": ("Cutting Plan No", ["inv_cutting_plan_no", "cutting_plan_no"]),
    "picked": ("Picked", ["inv_picked", "picked"]),
    "entry_type": ("Entry Type", ["inv_entry_type", "entry_type"]),
    "document_type": ("Document Type", ["inv_document_type", "document_type"]),
    "order_type": ("Order Type", ["inv_order_type", "order_type"]),
    "order_no": ("Order No", ["inv_order_no", "order_no"]),
    "order_line_no": ("Order Line No", ["inv_order_line_no", "order_line_no"]),
    "prod_order_comp_line_no": ("Prod. Order Comp. Line No", ["inv_prod_order_comp_line_no", "prod_order_comp_line_no"]),
    "project_no": ("Project No", ["inv_project_no", "project_no"]),
    "project_task_no": ("Project Task No", ["inv_project_task_no", "project_task_no"]),
    "weight": ("Weight", ["inv_weight", "weight"]),
    "posting_date": ("Posting Date", ["inv_posting_date", "posting_date"]),
    "date": ("Date", ["inv_date", "date"]),
    "open_flag": ("Open", ["inv_open_flag", "open_flag"]),
    "drop_shipment": ("Drop Shipment", ["inv_drop_shipment", "drop_shipment"]),
    "assemble_to_order": ("Assemble To Order", ["inv_assemble_to_order", "assemble_to_order"]),
    "shipped_qty_not_returned": ("Shipped Qty. Not Returned", ["inv_shipped_qty_not_returned", "shipped_qty_not_returned"]),
    "inventory_by_location": ("Inventory By Location", ["inv_inventory_by_location", "inventory_by_location"]),
    "inventory": ("Inventory", ["inv_inventory", "inventory"]),
    "remaining_quantity": ("Remaining Quantity", ["inv_remaining_quantity", "remaining_quantity"]),
    "reserved_quantity": ("Reserved Quantity", ["inv_reserved_quantity", "reserved_quantity"]),
    "invoiced_quantity": ("Invoiced Quantity", ["inv_invoiced_quantity", "invoiced_quantity"]),
    "qty_per_unit_of_measure": ("Qty. per Unit of Measure", ["inv_qty_per_unit_of_measure", "qty_per_unit_of_measure"]),
    "expiration_date": ("Expiration Date", ["inv_expiration_date", "expiration_date"]),
    "sales_amount_expected": ("Sales Amount (Expected)", ["inv_sales_amount_expected", "sales_amount_expected"]),
    "sales_amount_actual": ("Sales Amount (Actual)", ["inv_sales_amount_actual", "sales_amount_actual"]),
    "cost_amount_expected": ("Cost Amount (Expected)", ["inv_cost_amount_expected", "cost_amount_expected"]),
    "cost_amount_actual": ("Cost Amount (Actual)", ["inv_cost_amount_actual", "cost_amount_actual"]),
    "cost_amount_non_invtbl": ("Cost Amount (Non-Invtbl.)", ["inv_cost_amount_non_invtbl", "cost_amount_non_invtbl"]),
    "cost_amount_expected_acy": ("Cost Amount (Expected) (ACY)", ["inv_cost_amount_expected_acy", "cost_amount_expected_acy"]),
    "cost_amount_actual_acy": ("Cost Amount (Actual) (ACY)", ["inv_cost_amount_actual_acy", "cost_amount_actual_acy"]),
    "cost_amount_non_invtbl_acy": ("Cost Amount (Non-Invtbl.)(ACY)", ["inv_cost_amount_non_invtbl_acy", "cost_amount_non_invtbl_acy"]),
    "unitcost_cwt": ("UnitCost / CWT", ["inv_unitcost_cwt", "unitcost_cwt"]),
    "country_of_melt": ("Country of Melt", ["mtr_country_of_melt", "inv_country_of_melt", "country_of_melt"]),
    "country_of_manufacture": ("Country of Manufacture", ["mtr_country_of_manufacture", "inv_country_of_manufacture", "country_of_manufacture"]),
    "c": ("C", ["mtr_c", "c_element"]),
    "mn": ("Mn", ["mtr_mn", "mn_element"]),
    "si": ("Si", ["mtr_si", "si_element"]),
    "p": ("P", ["mtr_p", "p_element"]),
    "s": ("S", ["mtr_s", "s_element"]),
    "b": ("B", ["mtr_b", "b_element"]),
    "v": ("V", ["mtr_v", "v_element"]),
    "nb": ("Nb", ["mtr_nb", "nb_element"]),
    "ti": ("Ti", ["mtr_ti", "ti_element"]),
    "al": ("Al", ["mtr_al", "al_element"]),
    "ca": ("Ca", ["mtr_ca", "ca_element"]),
    "zr": ("Zr", ["mtr_zr", "zr_element"]),
    "zn": ("Zn", ["mtr_zn", "zn_element"]),
    "sn": ("Sn", ["mtr_sn", "sn_element"]),
    "cu": ("Cu", ["mtr_cu", "cu_element"]),
    "ni": ("Ni", ["mtr_ni", "ni_element"]),
    "cr": ("Cr", ["mtr_cr", "cr_element"]),
    "mo": ("Mo", ["mtr_mo", "mo_element"]),
    "n": ("N", ["mtr_n", "n_element"]),
    "ce": ("CE", ["mtr_ce", "ce"]),
    "yield_strength": ("Yield Strength", ["mtr_yield_strength", "yield_strength"]),
    "tensile_strength": ("Tensile Strength", ["mtr_tensile_strength", "tensile_strength"]),
    "elongation": ("Elongation", ["mtr_elongation", "elongation"]),
    "reduction_area": ("Reduction Area", ["mtr_reduction_area", "reduction_area"]),
    "hardness": ("Hardness", ["mtr_hardness", "hardness"]),
    "thickness": ("Thickness", ["mtr_thickness", "thickness"]),
    "impact_charpy": ("Impact Charpy", ["mtr_impact_average", "mtr_impact_charpy", "impact_charpy"]),
    "impact_test_temp": ("Impact Test Temp", ["mtr_impact_test_temp", "impact_test_temp"]),
    "impact_coupon_size": ("Impact Coupon Size", ["mtr_impact_coupon_size", "impact_coupon_size"]),
    "impact_specimen_1": ("Impact Specimen 1", ["mtr_impact_specimen_1", "impact_specimen_1"]),
    "impact_specimen_2": ("Impact Specimen 2", ["mtr_impact_specimen_2", "impact_specimen_2"]),
    "impact_specimen_3": ("Impact Specimen 3", ["mtr_impact_specimen_3", "impact_specimen_3"]),
    "impact_average": ("Impact Average", ["mtr_impact_average", "impact_average"]),
    "plate_dimension": ("Plate Dimension", ["inv_dimensions", "dimensions"]),
    "dimensions": ("Dimensions", ["inv_dimensions", "dimensions"]),
    "direction": ("Direction", ["mtr_direction", "direction"]),
    "yield_value": ("Yield", ["inv_yield_value", "yield_value"]),
    "revision": ("Revision", ["inv_revision", "revision"]),
    "laser_quality": ("Laser Quality", ["inv_laser_quality", "laser_quality"]),
    "drawing": ("Drawing", ["inv_drawing", "drawing"]),
    "return_reason_code": ("Return Reason Code", ["inv_return_reason_code", "return_reason_code"]),
    "source_file": ("Source File", ["inv_source_file", "source_file"]),
    "image_path": ("Image Path", ["inv_image_path", "image_path"]),
}


def _sort_grade_records(records):
    return sorted(
        records or [],
        key=lambda row: _grade_specificity(row.get("mtr_grade")),
        reverse=True,
    )


def _searchable_field_names(model):
    fields = []
    for name, field in model._fields.items():
        if name in {"message_ids", "message_follower_ids", "activity_ids"}:
            continue
        if name.startswith("message_") or name.startswith("activity_"):
            continue
        if field.type in ("one2many", "many2many"):
            continue
        fields.append(name)
    return fields


def _infer_target_field(message, filters=None):
    text = (message or "").lower()
    patterns = [
        ("grade", r"\bgrade\b|\bspecification\b"),
        ("manufacturer", r"\bmanufacturer\b|\bmfg\b|\bmill\b"),
        ("certificate_number", r"\bcertificate(?: number| no| #)?\b|\bcert\b|\bmt[0-9a-z]+\b"),
        ("certificate_date", r"\bcertificate date\b|\bcert date\b"),
        ("piece_no", r"\bno of pieces\b|\bnumber of pieces\b|\bpieces? available\b|\bhow many pieces\b|\bpiece(?: number| no| #)?\b"),
        ("batch_number", r"\bbatch(?: number| no| #)?\b|\bbn\b"),
        ("heat_number", r"\bheat(?: number| no| #)?\b"),
        ("lot_number", r"\blot(?: number| no| #)?\b"),
        ("item_no", r"\bitem(?: number| no| #)?\b"),
        ("slab_number", r"\bslab(?: number| no| #)?\b"),
        ("location_code", r"\blocation(?: code)?\b"),
        ("quantity", r"\bquantity\b|\bqty\b"),
        ("unit_of_measure_code", r"\buom\b|\bunit of measure\b|\bunit\b"),
        ("document_no", r"\bdocument(?: number| no| #)?\b|\bdoc\b"),
        ("variant_code", r"\bvariant\b"),
        ("description", r"\bdescription\b"),
        ("description_2", r"\bdescription 2\b"),
        ("item_description", r"\bitem description\b"),
        ("source_description", r"\bsource description\b"),
        ("source_order_no", r"\bsource order\b"),
        ("serial_no", r"\bserial(?: number| no| #)?\b"),
        ("package_no", r"\bpackage(?: number| no| #)?\b"),
        ("weight", r"\bweight\b"),
        ("posting_date", r"\bposting date\b|\bdate\b"),
        ("country_of_melt", r"\bcountry of melt\b|\bmelt\b"),
        ("country_of_manufacture", r"\bcountry of manufacture\b|\bmanufacture\b"),
        ("c", r"\bcarbon\b|\bc\b"),
        ("mn", r"\bmanganese\b|\bmn\b"),
        ("si", r"\bsilicon\b|\bsi\b"),
        ("p", r"\bphosphorus\b|\bp\b"),
        ("s", r"\bsulfur\b|\bsulphur\b|\bs\b"),
        ("b", r"\bboron\b|\bb\b"),
        ("v", r"\bvanadium\b|\bv\b"),
        ("nb", r"\bniobium\b|\bnb\b"),
        ("ti", r"\btitanium\b|\bti\b"),
        ("al", r"\baluminum\b|\baluminium\b|\bal\b"),
        ("ca", r"\bcalcium\b|\bca\b"),
        ("zr", r"\bzirconium\b|\bzr\b"),
        ("zn", r"\bzinc\b|\bzn\b"),
        ("sn", r"\btin\b|\bsn\b"),
        ("cu", r"\bcopper\b|\bcu\b"),
        ("ni", r"\bnickel\b|\bni\b"),
        ("cr", r"\bchromium\b|\bcr\b"),
        ("mo", r"\bmolybdenum\b|\bmo\b"),
        ("n", r"\bnitrogen\b|\bn\b"),
        ("ce", r"\bce\b|\bcarbon equivalent\b|\bchemical equival(?:ency|ence)\b"),
        ("yield_strength", r"\byield strength\b|\bys\b"),
        ("tensile_strength", r"\btensile strength\b|\buts\b"),
        ("elongation", r"\belongation\b|\belong\b"),
        ("reduction_area", r"\breduction area\b|\bra\b"),
        ("hardness", r"\bhardness\b|\bhrb\b|\bhrc\b"),
        ("thickness", r"\bthickness\b|\bthk\b"),
        ("impact_charpy", r"\bcharpy\b|\bimpact charpy\b"),
        ("impact_test_temp", r"\bimpact test temp\b|\bimpact temp\b|\btest temp\b|\btest temperature\b"),
        ("impact_coupon_size", r"\bimpact coupon size\b"),
        ("impact_specimen_1", r"\bimpact specimen 1\b"),
        ("impact_specimen_2", r"\bimpact specimen 2\b"),
        ("impact_specimen_3", r"\bimpact specimen 3\b"),
        ("impact_average", r"\bimpact average\b|\bimpact\b"),
        ("plate_dimension", r"\bplate dimension\b"),
        ("dimensions", r"\bdimensions\b"),
        ("direction", r"\bdirection\b|\bdir\b"),
    ]
    for key, pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return key

    # If AI already proposed a single non-batch filter, use that as the field request.
    for entry in filters or []:
        field = (entry.get("field") or "").strip()
        if field and field not in ("batch_number", "heat_number", "inventory_heat_number"):
            return field
    return ""


# Always restrict chatbot searches to records that have a matched MTR.
_MATCHED_ONLY_DOMAIN = [("join_status", "=", "Matched")]

_CLAUDE_SYSTEM_PROMPT = """\
You are an intelligent assistant for Brannon Steel's MTR (Mill Test Report) inventory system.
You have direct access to the live database via the query_database tool.
You can answer any question, generate reports, perform compliance analysis, and provide business insights.

DATABASE SCHEMA — mtr_inventory_join_report
============================================
This is the ONLY table you query. Every column name is listed exactly as it appears.

STATUS & IDENTITY
  id                       -- always SELECT this; needed for clickable record cards
  join_status              -- 'Matched' or 'Missing MTR'
  join_priority

INVENTORY COLUMNS (prefix: inv_)
  inv_lot_number           -- inventory lot number
  inv_heat_number          -- heat number from Business Central inventory
  inv_slab_number          -- slab number
  inv_item_no              -- item/product number
  inv_dimensions           -- plate dimensions as stored in inventory (e.g. "40,120")
  inv_quantity
  inv_weight
  inv_piece_no
  inv_location_code
  inv_item_description
  inv_description
  inv_grade                -- grade from inventory system
  inv_country_of_melt
  inv_country_of_manufacture
  inv_document_no
  inv_posting_date

MTR CERTIFICATE COLUMNS (prefix: mtr_)
  mtr_id                   -- FK to mtr_data record
  mtr_heat_number          -- heat number from MTR certificate
  mtr_batch_number         -- batch number from MTR certificate
  mtr_certificate_number   -- certificate number
  mtr_certificate_date
  mtr_grade                -- grade on the MTR certificate (use this for grade questions)
  mtr_manufacturer
  mtr_thickness            -- certified thickness from MTR — ALWAYS use for thickness questions
  mtr_direction
  mtr_country_of_melt
  mtr_country_of_manufacture
  mtr_uploaded_at

MTR CHEMISTRY (all numeric, may be NULL)
  mtr_c, mtr_mn, mtr_si, mtr_p, mtr_s, mtr_b, mtr_v, mtr_nb, mtr_ti,
  mtr_al, mtr_ca, mtr_zr, mtr_zn, mtr_sn, mtr_cu, mtr_ni, mtr_cr, mtr_mo,
  mtr_n, mtr_ce

MTR MECHANICAL (all numeric, may be NULL)
  mtr_yield_strength, mtr_tensile_strength, mtr_elongation,
  mtr_reduction_area, mtr_hardness

MTR IMPACT (all numeric, may be NULL)
  mtr_impact_test_temp, mtr_impact_charpy, mtr_impact_coupon_size,
  mtr_impact_specimen_1, mtr_impact_specimen_2, mtr_impact_specimen_3,
  mtr_impact_average

ADDITIONAL TABLES (for spec lookup only)
  mtr_specification: id, name, customer, status
  mtr_spec_rule_branch: id, spec_id, name, grades, astm_equivalent

QUERY RULES
===========
- ONLY query mtr_inventory_join_report. Do NOT query mtr_data or inventory directly.
- ALWAYS filter WHERE join_status = 'Matched' unless user asks about missing MTRs.
- ALWAYS include the id column so records appear as clickable cards.
- Use ILIKE for text matching: mtr_grade ILIKE '%50%'
- inv_dimensions stores values like "40,120" — use ILIKE '%40%' or '%120%' to search.
- mtr_thickness is the certified MTR thickness — always use it for thickness questions.
- For general record lists LIMIT to 50 rows; for spec/grade matching queries use LIMIT 500 to return all matches.
- No LIMIT needed for COUNT/aggregate queries.
- CRITICAL: column names are exactly as listed above. Do NOT invent column names like
  "grade", "dimension", "thickness" — always use the full prefixed names like
  mtr_grade, inv_dimensions, mtr_thickness.

CAPABILITIES
============
You can:
- Look up specific records by batch, heat, grade, certificate number, dimensions, etc.
- Count, aggregate, and analyse inventory data
- Generate compliance reports (which heats pass/fail specific requirements)
- Identify gaps: missing chem, mech, impact data
- Compare thicknesses, grades, chemical compositions across batches
- Summarise inventory by grade, manufacturer, location, thickness range
- Answer "what specs does batch X qualify for?" by querying chemistry/mechanical data
- Run full spec matching: when the user asks to match inventory against a spec, use run_spec_match

SPEC MATCHING
=============
Use run_spec_match when the user:
- Asks "find plates/inventory matching spec X"
- Asks "which plates qualify for [spec name]?"
- Asks "run spec match for [name]"
- Asks "what matches ASTM A36?" (or any grade/spec name)
To find available spec names, query: SELECT id, name, customer FROM mtr_specification WHERE status = 'active' LIMIT 50
Then call run_spec_match with the exact spec name.

FORMAT
======
- Use Markdown for all responses: ## headers, bullet lists, **bold**, tables
- For record lists use a Markdown table with | separators
- Be concise but thorough
- When referencing specific records in your answer, ALWAYS query mtr_inventory_join_report
  with SELECT id, ... so those records automatically appear as clickable cards below your answer.
  The user can then click "Open Join Report" on any card to view the full record.
- When showing records in a table, include: mtr_batch_number, mtr_heat_number, mtr_grade,
  mtr_thickness, inv_dimensions, and the relevant status column(s).
"""

_CLAUDE_TOOLS = [
    {
        "name": "query_database",
        "description": (
            "Run a read-only SELECT (or WITH ... SELECT) query against the Brannon MTR database. "
            "Returns JSON rows. Always LIMIT results; never mutate data."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "A PostgreSQL SELECT statement.",
                }
            },
            "required": ["sql"],
        },
    },
    {
        "name": "run_spec_match",
        "description": (
            "Run the full spec-matching engine against Brannon inventory for a named specification. "
            "Returns how many records matched and attaches clickable result cards. "
            "Use this whenever the user wants to find inventory that qualifies for a particular spec, grade standard, or customer requirement."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "spec_name": {
                    "type": "string",
                    "description": "The exact name of the spec in the system (e.g. 'ASTM A36', 'API 5L X65'). Use query_database on mtr_specification first if unsure.",
                },
                "branch_name": {
                    "type": "string",
                    "description": "Optional: the branch/grade variant name within the spec (e.g. 'Grade B', 'Type 1'). Omit to match all branches.",
                },
            },
            "required": ["spec_name"],
        },
    },
]


def _claude_agent_loop(env, messages, api_key, model, system_prompt=None):
    """Shared Claude agentic loop with SQL query tool. Returns (answer_text, join_report_ids)."""
    if system_prompt is None:
        system_prompt = _CLAUDE_SYSTEM_PROMPT
    join_ids = []
    last_error = None

    for _step in range(12):
        try:
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": 4096,
                    "system": system_prompt,
                    "tools": _CLAUDE_TOOLS,
                    "messages": messages,
                },
                timeout=90,
            )
            resp.raise_for_status()
        except Exception as exc:
            _logger.error("Claude API request failed: %s", exc)
            return _("Claude API request failed: %s") % exc, []

        data = resp.json()
        stop_reason = data.get("stop_reason")
        content = data.get("content", [])

        if stop_reason == "end_turn":
            answer = "".join(
                block.get("text", "") for block in content if block.get("type") == "text"
            )
            return answer, join_ids

        if stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": content})
            tool_results = []
            for block in content:
                if block.get("type") != "tool_use":
                    continue
                tool_name = block.get("name", "")
                tool_input = block.get("input", {})

                if tool_name == "query_database":
                    sql = tool_input.get("sql", "").strip()
                    sql_upper = sql.upper().lstrip()
                    if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
                        result_text = "Error: only SELECT queries are permitted."
                    else:
                        try:
                            env.cr.execute(sql)
                            rows = env.cr.fetchall()
                            cols = [d[0] for d in (env.cr.description or [])]
                            rows_as_dicts = [dict(zip(cols, row)) for row in rows]
                            if "mtr_inventory_join_report" in sql.lower() and "id" in cols:
                                # Replace (not extend) so only the final qualifying query's
                                # IDs become result cards, not every exploratory query.
                                new_ids = [r["id"] for r in rows_as_dicts if r.get("id")]
                                if new_ids:
                                    join_ids = new_ids
                            result_text = json.dumps(rows_as_dicts, default=str)
                        except Exception as exc:
                            _logger.warning("Claude tool SQL error: %s | SQL: %s", exc, sql[:300])
                            env.cr.rollback()
                            result_text = "Query error: %s. Use exact column names from schema (e.g. mtr_grade, inv_dimensions, mtr_thickness)." % exc

                elif tool_name == "run_spec_match":
                    spec_name = tool_input.get("spec_name", "").strip()
                    branch_name = tool_input.get("branch_name", "").strip() or None
                    try:
                        # Resolve optional branch id from branch_name
                        branch_id = None
                        if branch_name:
                            env.cr.execute(
                                "SELECT srb.id FROM mtr_spec_rule_branch srb "
                                "JOIN mtr_specification sp ON sp.id = srb.spec_id "
                                "WHERE sp.name ILIKE %s AND srb.name ILIKE %s LIMIT 1",
                                (spec_name, branch_name),
                            )
                            row = env.cr.fetchone()
                            if row:
                                branch_id = row[0]

                        match_result = _run_spec_match(env, spec_name=spec_name, branch_id=branch_id)
                        # Collect join_ids from result cards
                        for r in match_result.get("results", []):
                            jid = r.get("join_id")
                            if jid:
                                join_ids.append(jid)
                        count = len(match_result.get("results", []))
                        answer_preview = match_result.get("answer", "")
                        result_text = json.dumps({
                            "matched_count": count,
                            "answer": answer_preview,
                            "note": "Result cards will be shown to the user automatically.",
                        })
                    except Exception as exc:
                        _logger.warning("Claude spec match error: %s", exc)
                        result_text = "Spec match error: %s" % exc
                else:
                    result_text = "Unknown tool: %s" % tool_name

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block["id"],
                    "content": result_text,
                })
            messages.append({"role": "user", "content": tool_results})
        else:
            # Unexpected stop_reason — extract any text Claude returned and return it
            text_so_far = "".join(
                block.get("text", "") for block in content if block.get("type") == "text"
            )
            _logger.warning("Claude unexpected stop_reason=%s text=%s", stop_reason, text_so_far[:200])
            if text_so_far:
                return text_so_far, join_ids
            break

    # Return whatever text Claude accumulated if we ran out of iterations
    last_assistant = next(
        (m for m in reversed(messages) if m.get("role") == "assistant"),
        None,
    )
    if last_assistant:
        content_blocks = last_assistant.get("content", [])
        if isinstance(content_blocks, list):
            text = "".join(b.get("text", "") for b in content_blocks if isinstance(b, dict) and b.get("type") == "text")
            if text:
                _logger.warning("Claude hit iteration limit; returning partial answer")
                return text, join_ids
    _logger.error("Claude agent loop exhausted with no answer. Steps=%d join_ids=%d", _step + 1, len(join_ids))
    return _("I wasn't able to complete that query. Please try rephrasing your question."), join_ids


def _call_claude_agent(env, message, api_key, model="claude-opus-4-5", history=None):
    """Convenience wrapper for text-only chat messages with optional conversation history."""
    messages = []
    # Rebuild prior turns from history so Claude has conversation context
    for turn in (history or []):
        role = turn.get("role") if isinstance(turn, dict) else None
        text = turn.get("text") if isinstance(turn, dict) else None
        if role in ("user", "assistant") and text:
            messages.append({"role": role, "content": str(text)})
    messages.append({"role": "user", "content": message})
    return _claude_agent_loop(env, messages, api_key, model)


def _call_openai_parser(message, api_key, model):
    system_prompt = (
        "You are an expert search planner for MTR and inventory data. "
        "Infer the user's intent from the meaning of the sentence, not from simple keyword matching. "
        "If the message uses a bare element symbol followed by a value, treat it as that element field. "
        "Examples: 'MO 000' -> mo, 'C 0.17' -> c, 'NB 0.03' -> nb, 'MN 1.2' -> mn. "
        "Examples: 'What is the grade of heat 55-0700?' -> target_field grade, filter heat_number 55-0700. "
        "Examples: 'What is the chemical equivalency of heat 0005T6-03?' -> target_field ce, filter heat_number 0005T6-03. "
        "Examples: 'MT064636' -> target_field certificate_number, filter certificate_number MT064636. "
        "Examples: 'test temperature is 1.0' -> target_field impact_test_temp, filter impact_test_temp 1.0. "
        "Examples: 'impact test temperature is 1' -> target_field impact_test_temp, filter impact_test_temp 1. "
        "Examples: 'mtr where we have more than 9 pieces available' -> target_field piece_no, filter piece_no > 9. "
        "Examples: 'no of pieces more than 9' -> target_field piece_no, filter piece_no > 9. "
        "Examples: 'What are the chemical properties of batch number CZ8954?' -> return the chemistry block for batch_number CZ8954. "
        "Examples: 'Show the mechanical properties of batch number CZ8954.' -> return the mechanical block for batch_number CZ8954. "
        "Examples: 'Show the impact values of batch number CZ8954.' -> return the impact block for batch_number CZ8954. "
        "Do not default these queries to batch_number unless the user explicitly says batch. "
        "Use the data model guide below to understand what values look like in real records. "
        "Return ONLY valid JSON with this shape: "
        "{\"filters\":[{\"field\":\"batch_number\",\"op\":\"=\",\"value\":\"B100\"}],"
        "\"target_field\":\"grade\","
        "\"text_query\":\"optional\","
        "\"limit\":20}. "
        "Map common aliases to fields: "
        "c/carbon -> c, mn/manganese -> mn, si/silicon -> si, p/phosphorus -> p, s/sulfur -> s, "
        "cu/copper -> cu, ni/nickel -> ni, cr/chromium -> cr, mo/molybdenum -> mo, n/nitrogen -> n, "
        "yield strength/ys -> yield_strength, tensile/uts -> tensile_strength, "
        "elongation/elong -> elongation, reduction area/ra -> reduction_area, "
        "hardness/hrb/hrc -> hardness, impact/charpy -> impact_average. "
        "dimensions/plate_dimension/plate dimension -> dimensions (inventory side only, never MTR). "
        "All searches are performed against the join report only. Do not reference MTR-only tables. "
        "Primary identifier is batch_number. heat_number is legacy fallback only. "
        "Valid fields include MTR and inventory fields such as: batch_number, heat_number, piece_no, grade, manufacturer, "
        "certificate_number, certificate_date, country_of_melt, country_of_manufacture, lot_number, item_no, slab_number, "
        "inventory_heat_number, inventory_grade, date, posting_date, location_code, quantity, unit_of_measure_code, "
        "document_no, wsi_variant_code, dimensions, internal_bin, cost_amount_actual, description_2, origin_code, picked, "
        "cutting_plan_no, image_path, entry_type, document_type, drawing, yield_value, revision, laser_quality, unitcost_cwt, "
        "piece_number, variant_code, description, return_reason_code, serial_no, package_no, invoiced_quantity, "
        "inventory_by_location, inventory, expiration_date, remaining_quantity, shipped_qty_not_returned, reserved_quantity, "
        "qty_per_unit_of_measure, sales_amount_expected, sales_amount_actual, cost_amount_expected, cost_amount_non_invtbl, "
        "item_description, cost_amount_expected_acy, cost_amount_actual_acy, completely_invoiced, cost_amount_non_invtbl_acy, "
        "assemble_to_order, drop_shipment, open_flag, order_type, order_no, order_line_no, prod_order_comp_line_no, entry_no, "
        "project_no, project_task_no, source_type, source_no, source_description, source_order_no, weight, c, mn, si, p, s, b, v, "
        "nb, ti, al, ca, zr, zn, sn, cu, ni, cr, mo, n, ce, yield_strength, tensile_strength, elongation, reduction_area, "
        "hardness, thickness, impact_charpy, impact_test_temp, impact_coupon_size, impact_specimen_1, impact_specimen_2, "
        "impact_specimen_3, impact_average, dimensions, direction. "
        "Valid ops: =, !=, >=, <=, >, <, ilike, not ilike. "
        "If user includes ranges like '>= 0.2', use the correct op. "
        "If you cannot extract structured filters, put the full query in text_query. "
        + _SEARCH_SCHEMA_GUIDE
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
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
        json=payload,
        timeout=25,
    )
    response.raise_for_status()
    data = response.json()
    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )
    return _extract_json(content), content


def _call_openai_answerer(message, api_key, model, source_label, filters, results, text_query):
    compact_results = []
    for row in results or []:
        compact_results.append({
            "join_status": row.get("join_status"),
            "mtr_batch_number": row.get("mtr_batch_number"),
            "mtr_heat_number": row.get("mtr_heat_number"),
            "mtr_grade": row.get("mtr_grade"),
            "mtr_manufacturer": row.get("mtr_manufacturer"),
            "mtr_certificate_number": row.get("mtr_certificate_number"),
            "mtr_certificate_date": row.get("mtr_certificate_date"),
            "mtr_c": row.get("mtr_c"),
            "mtr_mn": row.get("mtr_mn"),
            "mtr_si": row.get("mtr_si"),
            "mtr_p": row.get("mtr_p"),
            "mtr_s": row.get("mtr_s"),
            "mtr_b": row.get("mtr_b"),
            "mtr_v": row.get("mtr_v"),
            "mtr_nb": row.get("mtr_nb"),
            "mtr_ti": row.get("mtr_ti"),
            "mtr_al": row.get("mtr_al"),
            "mtr_ca": row.get("mtr_ca"),
            "mtr_zr": row.get("mtr_zr"),
            "mtr_zn": row.get("mtr_zn"),
            "mtr_sn": row.get("mtr_sn"),
            "mtr_cu": row.get("mtr_cu"),
            "mtr_ni": row.get("mtr_ni"),
            "mtr_cr": row.get("mtr_cr"),
            "mtr_mo": row.get("mtr_mo"),
            "mtr_n": row.get("mtr_n"),
            "mtr_ce": row.get("mtr_ce"),
            "mtr_yield_strength": row.get("mtr_yield_strength"),
            "mtr_tensile_strength": row.get("mtr_tensile_strength"),
            "mtr_elongation": row.get("mtr_elongation"),
            "mtr_reduction_area": row.get("mtr_reduction_area"),
            "mtr_hardness": row.get("mtr_hardness"),
            "mtr_thickness": row.get("mtr_thickness"),
            "mtr_impact_charpy": row.get("mtr_impact_charpy"),
            "mtr_impact_test_temp": row.get("mtr_impact_test_temp"),
            "mtr_impact_coupon_size": row.get("mtr_impact_coupon_size"),
            "mtr_impact_average": row.get("mtr_impact_average"),
            "mtr_country_of_melt": row.get("mtr_country_of_melt"),
            "mtr_country_of_manufacture": row.get("mtr_country_of_manufacture"),
            "inv_lot_number": row.get("inv_lot_number"),
            "inv_item_no": row.get("inv_item_no"),
            "inv_heat_number": row.get("inv_heat_number"),
            "inv_slab_number": row.get("inv_slab_number"),
        })

    system_prompt = (
        "You are the answer writer for an MTR chatbot. "
        "Use the provided search results to answer the user's question naturally and concisely. "
        "Do not invent any values. If there are no results, say so clearly and suggest the next best search only if it is obvious from the query. "
        "If the question asks for a single value like grade, manufacturer, certificate number, or a chemistry value, state that value directly. "
        "Examples: 'What is the grade of heat 55-0700?' -> 'Heat 55-0700 has grade A36.' "
        "Examples: 'MO 000' -> 'No records found for Mo = 0.00000.' "
        "Examples: 'What is the manufacturer of heat 55-0700?' -> 'Heat 55-0700 was manufactured by ...'. "
        "If there are multiple results, summarize the relevant values and mention that multiple matches were found. "
        "For thickness questions, always use mtr_thickness (the certified value from the MTR document) as the primary answer. "
        "Do not derive thickness from dimensions or any inventory field. "
        "Use the data model guide below to make the response sound like it came from the actual record layout. "
        "Return plain text only. "
        + _SEARCH_SCHEMA_GUIDE
    )
    user_prompt = {
        "question": message,
        "source": source_label,
        "filters": filters or [],
        "text_query": text_query,
        "results": compact_results,
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=False)},
        ],
        "temperature": 0.2,
    }
    headers = {
        "Authorization": "Bearer %s" % api_key,
        "Content-Type": "application/json",
    }
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=25,
    )
    response.raise_for_status()
    data = response.json()
    return (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
        .strip()
    )


def _call_openai_match_summary(api_key, model, spec_name, rows, result_count):
    compact_rows = []
    for row in rows or []:
        compact_rows.append({
            "mtr_batch_number": row.get("mtr_batch_number"),
            "mtr_heat_number": row.get("mtr_heat_number"),
            "mtr_grade": row.get("mtr_grade"),
            "inv_lot_number": row.get("inv_lot_number"),
            "inv_heat_number": row.get("inv_heat_number"),
            "inv_item_no": row.get("inv_item_no"),
            "grade_match": row.get("grade_match"),
            "matched_grade_label": row.get("matched_grade_label"),
            "ce_value": row.get("ce_value"),
            "ce_max": row.get("ce_max"),
            "missing_notes": row.get("missing_notes"),
        })

    system_prompt = (
        "You are the MTR match summary writer. "
        "Write a concise but complete summary of the match results. "
        "Explain what matched and what the notes say, but do not invent status labels that were not provided. "
        "Do not mention chem/mech/impact/CE as separate status labels unless they appear explicitly in the provided data. "
        "If a grade alias matched, mention it. "
        "Do not invent any values. "
        "Use only the provided data. "
        "Return plain text only."
    )
    user_prompt = {
        "spec_name": spec_name,
        "result_count": result_count,
        "rows": compact_rows,
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=False)},
        ],
        "temperature": 0.2,
    }
    headers = {
        "Authorization": "Bearer %s" % api_key,
        "Content-Type": "application/json",
    }
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=25,
    )
    response.raise_for_status()
    data = response.json()
    return (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
        .strip()
    )


def _call_openai_filter_planner(api_key, model, spec_payload, message=""):
    system_prompt = (
        "You are the MTR filter-plan analyst for a spec planning bot. "
        "You receive a steel specification with branches, limits, condition rules, CE thresholds, and raw custom rules. "
        "Your job is to decide how the application should treat each rule at runtime. "
        "Do not write code. Do not invent missing rules. "
        "For each custom rule, choose one action: hard_filter, soft_filter, note, map_to_existing_field, needs_review. "
        "If a rule maps to a concrete field, fill mapped_field, mapped_operator, mapped_value_text, mapped_value_number, and mapped_value_unit. "
        "If a rule is only a reference, ASTM note, or compliance note that cannot be executed safely, mark it as note or needs_review. "
        "Use only real fields that already exist in the data model: grade, manufacturer, certificate_number, ce, thickness, dimensions, direction, "
        "yield_strength, tensile_strength, elongation, reduction_area, hardness, impact_test_temp, impact_coupon_size, impact_specimen_1, "
        "impact_specimen_2, impact_specimen_3, impact_average, country_of_melt, country_of_manufacture, batch_number, heat_number, lot_number, dimensions, weight. "
        "Return ONLY valid JSON with this shape: "
        "{"
        "\"answer\":\"\","
        "\"spec_name\":\"\","
        "\"primary_branch\":\"\","
        "\"branch_plans\":[{"
        "\"branch_key\":\"\","
        "\"branch_name\":\"\","
        "\"summary\":\"\","
        "\"hard_filters\":[{\"field\":\"\",\"operator\":\"\",\"value_text\":\"\",\"value_number\":null,\"value_unit\":\"\",\"reason\":\"\"}],"
        "\"soft_filters\":[{\"field\":\"\",\"operator\":\"\",\"value_text\":\"\",\"value_number\":null,\"value_unit\":\"\",\"reason\":\"\"}],"
        "\"custom_rule_plan\":[{\"label\":\"\",\"field_name\":\"\",\"operator\":\"\",\"value_text\":\"\",\"value_number\":null,\"value_unit\":\"\",\"decision\":\"\",\"mapped_field\":\"\",\"mapped_operator\":\"\",\"mapped_value_text\":\"\",\"mapped_value_number\":null,\"mapped_value_unit\":\"\",\"reason\":\"\"}],"
        "\"notes\":[\"\"],"
        "\"execution_order\":[\"\"],"
        "\"confidence\":0"
        "}],"
        "\"global_notes\":[\"\"],"
        "\"unresolved_rules\":[\"\"],"
        "\"questions\":[\"\"]"
        "}. "
        "If the user message is empty, produce the best overall filtering plan. "
        "If the user message asks a question, answer it in the answer field while keeping the plan consistent. "
        "The answer should be plain text, concise, and helpful. "
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "message": message or "",
                        "spec": spec_payload,
                    },
                    ensure_ascii=False,
                ),
            },
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
        json=payload,
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


def _call_openai_spec_match_decider(api_key, model, match_payload):
    system_prompt = (
        "You are an MTR specification match engine. "
        "The extracted spec may use arbitrary headers, table names, and field names. "
        "Interpret the specification semantically from the extracted branch data, then decide whether the candidate MTR and inventory record satisfy the selected branch. "
        "Do not rely on exact header names alone. Use the extracted rules, selector summary, branch_json, selector_json, chemistry limits, mechanical limits, impact limits, CE thresholds, conditional rules, and custom rules together. "
        "If the record clearly satisfies the extracted branch, return decision pass. If it clearly fails, return fail. If the spec is insufficient to decide, return needs_review. "
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
        "Keep the answer concise and plain text."
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps(match_payload, ensure_ascii=False),
            },
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
        json=payload,
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


def _format_filter_plan_answer(plan):
    if not isinstance(plan, dict):
        return _("No filtering plan could be generated.")

    lines = []
    answer = (plan.get("answer") or "").strip()
    if answer:
        lines.append(answer)

    spec_name = (plan.get("spec_name") or "").strip()
    if spec_name:
        lines.append(_("Spec: %s") % spec_name)

    primary_branch = (plan.get("primary_branch") or "").strip()
    if primary_branch:
        lines.append(_("Primary branch: %s") % primary_branch)

    for branch in plan.get("branch_plans") or []:
        if not isinstance(branch, dict):
            continue
        branch_name = (branch.get("branch_name") or branch.get("branch_key") or "").strip()
        summary = (branch.get("summary") or "").strip()
        header = branch_name
        if summary:
            header = "%s - %s" % (branch_name, summary) if branch_name else summary
        if header:
            lines.append("")
            lines.append(header)

        hard_filters = branch.get("hard_filters") or []
        if hard_filters:
            lines.append(_("Hard filters:"))
            for item in hard_filters:
                if not isinstance(item, dict):
                    continue
                reason = (item.get("reason") or "").strip()
                field = (item.get("field") or "").strip()
                operator = (item.get("operator") or "").strip()
                value = item.get("value_text")
                if value in (None, ""):
                    value = item.get("value_number")
                text = "%s %s %s" % (field, operator, value)
                if reason:
                    text = "%s (%s)" % (text, reason)
                lines.append("- %s" % text)

        soft_filters = branch.get("soft_filters") or []
        if soft_filters:
            lines.append(_("Soft filters:"))
            for item in soft_filters:
                if not isinstance(item, dict):
                    continue
                reason = (item.get("reason") or "").strip()
                field = (item.get("field") or "").strip()
                operator = (item.get("operator") or "").strip()
                value = item.get("value_text")
                if value in (None, ""):
                    value = item.get("value_number")
                text = "%s %s %s" % (field, operator, value)
                if reason:
                    text = "%s (%s)" % (text, reason)
                lines.append("- %s" % text)

        custom_rule_plan = branch.get("custom_rule_plan") or []
        if custom_rule_plan:
            lines.append(_("Custom rules:"))
            for item in custom_rule_plan:
                if not isinstance(item, dict):
                    continue
                label = (item.get("label") or "").strip()
                decision = (item.get("decision") or "").strip()
                mapped_field = (item.get("mapped_field") or "").strip()
                mapped_operator = (item.get("mapped_operator") or "").strip()
                mapped_value = item.get("mapped_value_text")
                if mapped_value in (None, ""):
                    mapped_value = item.get("mapped_value_number")
                reason = (item.get("reason") or "").strip()
                text = label or _("Custom rule")
                if decision:
                    text += " -> %s" % decision
                if mapped_field or mapped_operator or mapped_value not in (None, ""):
                    text += " [%s %s %s]" % (mapped_field, mapped_operator, mapped_value)
                if reason:
                    text += " (%s)" % reason
                lines.append("- %s" % text)

        notes = branch.get("notes") or []
        if notes:
            lines.append(_("Notes:"))
            for note in notes:
                if note not in (None, ""):
                    lines.append("- %s" % note)

    global_notes = plan.get("global_notes") or []
    if global_notes:
        lines.append("")
        lines.append(_("Global notes:"))
        for note in global_notes:
            if note not in (None, ""):
                lines.append("- %s" % note)

    unresolved = plan.get("unresolved_rules") or []
    if unresolved:
        lines.append("")
        lines.append(_("Unresolved rules:"))
        for item in unresolved:
            if item not in (None, ""):
                lines.append("- %s" % item)

    questions = plan.get("questions") or []
    if questions:
        lines.append("")
        lines.append(_("Questions:"))
        for item in questions:
            if item not in (None, ""):
                lines.append("- %s" % item)

    return "\n".join(lines).strip()


def _build_spec_filter_plan_context(spec):
    def _split_values(value):
        if value in (None, False, ""):
            return []
        if isinstance(value, (list, tuple, set)):
            items = []
            for item in value:
                items.extend(_split_values(item))
            return [item for item in items if item not in (None, "", False)]
        parts = re.split(r"[,\n;|]+", str(value))
        return [part.strip() for part in parts if part and part.strip()]

    def _safe_json(text):
        if not text:
            return {}
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {"value": parsed}
        except Exception:
            return {}

    branches = []
    for branch in spec.branch_ids.sorted(lambda b: (b.sequence or 10, b.id)):
        branches.append({
            "branch_key": branch.branch_key,
            "name": branch.name,
            "spec_type": branch.spec_type or "",
            "selector_summary": branch.selector_summary or "",
            "ai_summary": branch.ai_summary or "",
            "astm_equivalent": _split_values(branch.astm_equivalent),
            "grades": _split_values(branch.grades),
            "manufacturer_grades": _split_values(branch.manufacturer_grades),
            "approved_substitutes": _split_values(branch.approved_substitutes),
            "notes": branch.notes or "",
            "selector_json": _safe_json(branch.selector_json),
            "branch_json": _safe_json(branch.branch_json),
            "chem_limits": [
                {
                    "element": line.element,
                    "min_value": line.min_value,
                    "max_value": line.max_value,
                    "source": line.source,
                }
                for line in branch.branch_chem_limit_ids.sorted(lambda r: (r.id or 0))
            ],
            "mech_limits": [
                {
                    "property": line.property,
                    "min_value": line.min_value,
                    "max_value": line.max_value,
                    "unit": line.unit,
                    "specimen_size": line.specimen_size,
                }
                for line in branch.branch_mech_limit_ids.sorted(lambda r: (r.id or 0))
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
                for line in branch.branch_impact_limit_ids.sorted(lambda r: (r.id or 0))
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
                for line in branch.branch_condition_rule_ids.sorted(lambda r: (r.id or 0))
            ],
            "ce_thresholds": [
                {
                    "thickness_min": line.thickness_min,
                    "thickness_max": line.thickness_max,
                    "max_ce": line.max_ce,
                }
                for line in branch.branch_ce_threshold_ids.sorted(lambda r: (r.id or 0))
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
                for line in branch.branch_custom_rule_ids.sorted(lambda r: (r.id or 0))
            ],
        })

    return {
        "spec_id": spec.id,
        "spec_name": spec.name or "",
        "customer": spec.customer or "",
        "ce_formula": spec.ce_formula or "",
        "notes": spec.notes or "",
        "branches": branches,
    }


def _build_spec_match_context(spec, branch, mtr, inventory, mtr_values):
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

    return {
        "spec": {
            "id": spec.id,
            "name": spec.name or "",
            "customer": spec.customer or "",
            "ce_formula": spec.ce_formula or "",
            "notes": spec.notes or "",
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
            "plate_dimension",
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
        },
    }

class MtrModule(http.Controller):
    @http.route('/mtr_module/mtr_module/', auth='public')
    def index(self, **kw):
        return "Hello, world"

    @http.route('/mtr_module/mtr_module/objects/', auth='public')
    def list(self, **kw):
        return http.request.render('mtr_module.listing', {
            'root': '/mtr_module/mtr_module',
            'objects': http.request.env['mtr_module.mtr_module'].search([]),
        })

    @http.route('/mtr_module/mtr_module/objects/<model("mtr_module.mtr_module"):obj>/', auth='public')
    def object(self, obj, **kw):
        return http.request.render('mtr_module.object', {
            'object': obj
        })


class MtrChatbotController(http.Controller):
    @http.route("/mtr_module/mtr_chatbot", type="json", auth="user")
    def mtr_chatbot(self, message=None, debug_llm=False, spec_id=None, branch_id=None, history=None):
        if not message:
            return {"error": _("Please enter a question.")}

        env = request.env
        text = (message or "").strip()

        # Match command: "match <spec>" / "run match for <spec>" / "find plates for <spec>"
        lowered = text.lower()
        match_prefixes = ["match ", "run match ", "run match for ", "find plates for ", "find match for "]
        for prefix in match_prefixes:
            if lowered.startswith(prefix):
                spec_name = text[len(prefix):].strip()
                return _run_spec_match(env, spec_name, spec_id=spec_id, branch_id=branch_id)
        if lowered.startswith("match:"):
            spec_name = text.split(":", 1)[1].strip()
            return _run_spec_match(env, spec_name, spec_id=spec_id, branch_id=branch_id)

        params = env["ir.config_parameter"].sudo()

        # --- Claude agent (primary) ---
        anthropic_key = params.get_param("mtr_module.anthropic_api_key")
        if anthropic_key:
            anthropic_model = params.get_param("mtr_module.anthropic_model") or "claude-opus-4-5"
            answer, join_ids = _call_claude_agent(
                env, message, anthropic_key, anthropic_model, history=history or []
            )
            results = []
            if join_ids:
                report = env["mtr.inventory.join.report"]
                report_fields = _searchable_field_names(report)
                seen = set()
                for jid in join_ids:
                    if jid in seen:
                        continue
                    seen.add(jid)
                    rows = report.search_read([("id", "=", jid)], fields=report_fields, limit=1)
                    if rows:
                        row = rows[0]
                        row["join_id"] = row.get("id")
                        results.append(row)
            return {"answer": answer, "results": results}

        # --- OpenAI pipeline (fallback when no Anthropic key) ---
        api_key = params.get_param("mtr_module.openai_api_key")
        model = params.get_param("mtr_module.openai_model") or "gpt-4o-mini"

        if not api_key:
            return {
                "error": _(
                    "No AI key configured. "
                    "Set system parameter mtr_module.anthropic_api_key (Claude) "
                    "or mtr_module.openai_api_key (OpenAI fallback)."
                )
            }

        parsed = None
        raw_llm = None
        try:
            parsed, raw_llm = _call_openai_parser(message, api_key, model)
        except Exception as exc:
            _logger.warning("OpenAI parse failed: %s", exc)

        parsed = parsed or {"filters": [], "text_query": message, "limit": 20}
        filters = parsed.get("filters") or []
        target_field = (parsed.get("target_field") or "").strip().lower()
        text_query = (parsed.get("text_query") or "").strip()
        if text_query.lower() in ("optional", "none", "null"):
            text_query = ""
        limit = parsed.get("limit") or 20
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 20
        limit = max(1, min(limit, 50))
        guessed_target_field = False
        if not target_field:
            target_field = _infer_target_field(text, filters)
            guessed_target_field = bool(target_field)
        plate_dimension_requested = bool(re.search(r"\bplate dimension\b", text, re.IGNORECASE))
        if plate_dimension_requested:
            target_field = "plate_dimension"
            for entry in filters:
                field_key = (entry.get("field") or "").strip().lower()
                if field_key == "dimensions":
                    entry["field"] = "plate_dimension"
        property_topics = _detect_property_topics(text)

        if plate_dimension_requested:
            report = env["mtr.inventory.join.report"]
            report_fields = _searchable_field_names(report)
            inv_domain = _build_filters_domain(filters)
            dimension_value = _extract_dimension_value(text)
            if not dimension_value:
                dimension_value = next(
                    (
                        entry.get("value")
                        for entry in filters
                        if (entry.get("field") or "").strip().lower() in {"plate_dimension", "dimensions"}
                    ),
                    "",
                )
            variants = _dimension_query_variants(dimension_value)
            component_variants = _dimension_component_variants(dimension_value)
            if variants:
                inv_domain = _or_domain([("inv_dimensions", "ilike", variant) for variant in variants])
            if not inv_domain and component_variants:
                inv_domain = [("inv_dimensions", "ilike", part) for part in component_variants]
            if not inv_domain:
                inv_domain = _build_text_domain(text_query)

            results = report.search_read(_MATCHED_ONLY_DOMAIN + inv_domain, fields=report_fields, limit=limit) if inv_domain else []
            for row in results:
                row["join_id"] = row.get("id")
            if target_field == "grade":
                results = _sort_grade_records(results)
            if results and property_topics:
                answer = _format_property_blocks_answer(results, property_topics)
            elif results and target_field:
                answer = _format_exact_field_answer(results, target_field)
            elif results:
                answer = _format_exact_field_answer(results, "grade") or _format_direct_lookup_answer(
                    "",
                    results,
                    "Join Report",
                    message=text,
                )
            else:
                answer = _format_no_results_answer("Join Report", filters=filters, text_query=text_query)
            if guessed_target_field and answer:
                guessed_label = _FIELD_RESPONSE_MAP.get(target_field, (_humanize_field_name(target_field),))[0]
                if guessed_label and not answer.lower().startswith("i think you mean"):
                    answer = _("I think you mean %(field)s. %(answer)s") % {
                        "field": guessed_label,
                        "answer": answer,
                    }
            response = {
                "answer": answer,
                "results": results,
                "filters": filters,
                "text_query": text_query,
            }
            if debug_llm:
                response["debug_llm"] = raw_llm or ""
            return response

        domain = _build_filters_domain(filters)
        if not domain:
            domain = _build_text_domain(text_query)

        report = env["mtr.inventory.join.report"]
        report_fields = _searchable_field_names(report)
        results = []
        source_label = "Join Report"

        for candidate_filters in _expand_identifier_filter_variants(filters):
            candidate_domain = _build_filters_domain(candidate_filters)
            if not candidate_domain:
                continue
            candidate_results = report.search_read(
                _MATCHED_ONLY_DOMAIN + candidate_domain, fields=report_fields, limit=limit
            )
            for row in candidate_results:
                row["join_id"] = row.get("id")
            if candidate_results:
                results = candidate_results
                filters = candidate_filters
                break

        if target_field == "grade":
            results = _sort_grade_records(results)

        if results and property_topics:
            answer = _format_property_blocks_answer(results, property_topics)
        elif results and target_field:
            answer = _format_exact_field_answer(results, target_field)
        elif results:
            answer = _format_exact_field_answer(results, "grade") or _format_direct_lookup_answer(
                "",
                results,
                source_label,
                message=text,
            )
        else:
            answer = _format_no_results_answer(source_label, filters=filters, text_query=text_query)

        if guessed_target_field and answer:
            guessed_label = _FIELD_RESPONSE_MAP.get(target_field, (_humanize_field_name(target_field),))[0]
            if guessed_label and not answer.lower().startswith("i think you mean"):
                answer = _("I think you mean %(field)s. %(answer)s") % {
                    "field": guessed_label,
                    "answer": answer,
                }

        response = {
            "answer": answer,
            "results": results,
            "filters": filters,
            "text_query": text_query,
        }
        if debug_llm:
            response["debug_llm"] = raw_llm or ""
        return response

    @http.route("/mtr_module/spec_filter_plan", type="json", auth="user")
    def spec_filter_plan(self, spec_id=None, message=None, debug_llm=False):
        params = request.env["ir.config_parameter"].sudo()
        api_key = params.get_param("mtr_module.openai_api_key")
        model = params.get_param("mtr_module.openai_model") or "gpt-4o-mini"

        if not api_key:
            return {
                "error": _(
                    "OpenAI API key is not configured. "
                    "Set system parameter mtr_module.openai_api_key."
                )
            }

        if not spec_id:
            key = "mtr_module.last_spec_id.%s" % request.env.user.id
            spec_id = params.get_param(key) or ""

        try:
            spec_id = int(spec_id)
        except Exception:
            return {"error": _("Please select a specification first.")}

        spec = request.env["mtr.specification"].sudo().search([("id", "=", spec_id)], limit=1)
        if not spec:
            return {"error": _("Specification not found.")}

        spec_payload = _build_spec_filter_plan_context(spec)
        parsed = None
        raw_llm = None
        try:
            parsed, raw_llm = _call_openai_filter_planner(api_key, model, spec_payload, message or "")
        except Exception as exc:
            _logger.warning("OpenAI filter planner failed: %s", exc)

        parsed = parsed or {
            "spec_name": spec_payload.get("spec_name") or spec.name or "",
            "primary_branch": "",
            "branch_plans": [],
            "global_notes": [],
            "unresolved_rules": [],
            "questions": [],
            "answer": "",
        }
        parsed.setdefault("spec_name", spec_payload.get("spec_name") or spec.name or "")
        parsed.setdefault("primary_branch", "")
        parsed.setdefault("branch_plans", [])
        parsed.setdefault("global_notes", [])
        parsed.setdefault("unresolved_rules", [])
        parsed.setdefault("questions", [])
        parsed["answer"] = parsed.get("answer") or _format_filter_plan_answer(parsed)

        response = {
            "answer": parsed["answer"],
            "plan": parsed,
            "spec_id": spec.id,
            "spec_name": spec.name or "",
        }
        if debug_llm:
            response["debug_llm"] = raw_llm or ""
        return response

    @http.route("/mtr_module/spec_name", type="json", auth="user")
    def spec_name(self, spec_id=None):
        if not spec_id:
            return {"error": "missing_spec_id"}
        try:
            spec_id = int(spec_id)
        except Exception:
            return {"error": "invalid_spec_id"}
        spec = request.env["mtr.specification"].sudo().search([("id", "=", spec_id)], limit=1)
        if not spec:
            return {"error": "not_found"}
        return {"name": spec.name or ""}

    @http.route("/mtr_module/last_spec", type="json", auth="user")
    def last_spec(self):
        key = "mtr_module.last_spec_id.%s" % request.env.user.id
        spec_id = request.env["ir.config_parameter"].sudo().get_param(key) or ""
        try:
            spec_id_int = int(spec_id)
        except Exception:
            return {"error": "missing"}
        spec = request.env["mtr.specification"].sudo().search([("id", "=", spec_id_int)], limit=1)
        if not spec:
            return {"error": "missing"}
        return {"id": spec.id, "name": spec.name or ""}

    @http.route("/mtr_module/pending_match", type="json", auth="user")
    def pending_match(self):
        """Return and clear the pending auto-match spec set by Run Match. Returns {} if none."""
        params = request.env["ir.config_parameter"].sudo()
        key = "mtr_module.pending_match.%s" % request.env.user.id
        val = params.get_param(key) or ""
        if not val:
            return {}
        params.set_param(key, "")
        parts = val.split("|", 1)
        try:
            spec_id = int(parts[0])
        except Exception:
            return {}
        spec_name = parts[1] if len(parts) > 1 else ""
        if not spec_name:
            spec = request.env["mtr.specification"].sudo().search([("id", "=", spec_id)], limit=1)
            spec_name = spec.name or "" if spec else ""
        return {"id": spec_id, "name": spec_name}

    @http.route("/mtr_module/mtr_chatbot_pdf", type="http", auth="user", methods=["POST"], csrf=False)
    def mtr_chatbot_pdf(self, **post):
        """Extract text from a spec PDF and let Claude query the database for matching records."""
        import io
        try:
            import PyPDF2
        except ImportError:
            PyPDF2 = None

        env = request.env
        params = env["ir.config_parameter"].sudo()
        anthropic_key = params.get_param("mtr_module.anthropic_api_key")
        if not anthropic_key:
            return request.make_response(
                json.dumps({"error": "Anthropic API key not configured."}),
                headers=[("Content-Type", "application/json")],
            )

        pdf_file = request.httprequest.files.get("pdf")
        if not pdf_file:
            return request.make_response(
                json.dumps({"error": "No PDF file received."}),
                headers=[("Content-Type", "application/json")],
            )

        pdf_bytes = pdf_file.read()
        pdf_filename = getattr(pdf_file, "filename", "spec.pdf")

        # Extract text from PDF
        spec_text = ""
        if PyPDF2:
            try:
                reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
                pages = []
                for page in reader.pages:
                    text = page.extract_text() or ""
                    if text.strip():
                        pages.append(text.strip())
                spec_text = "\n\n".join(pages)
            except Exception as exc:
                _logger.warning("PDF text extraction failed: %s", exc)

        if not spec_text.strip():
            spec_text = "(PDF text could not be extracted — filename: %s)" % pdf_filename

        # Truncate to avoid token limits (~100k chars ≈ 25k tokens)
        if len(spec_text) > 80000:
            spec_text = spec_text[:80000] + "\n...[truncated]"

        anthropic_model = params.get_param("mtr_module.anthropic_model") or "claude-opus-4-5"

        system_prompt = (
            _CLAUDE_SYSTEM_PROMPT
            + "\n\nThe user has uploaded a specification PDF. Its full text is provided below. "
            "Read it carefully and extract all grade designations, chemistry limits (C, Mn, Si, P, S, Cr, Ni, Mo, V, Nb, Al, Ti, Cu, B, N, CE), "
            "mechanical requirements (yield strength, tensile strength, elongation, hardness), "
            "and impact requirements. "
            "Then query mtr_inventory_join_report to find ALL records that satisfy those requirements. "
            "Use LIMIT 500 in your SQL. Always include the id column. Filter WHERE join_status = 'Matched'. "
            "Show a summary of how many records matched and what criteria you used."
        )

        user_message = (
            "SPECIFICATION PDF: %s\n\n"
            "=== EXTRACTED SPEC TEXT ===\n%s\n=== END SPEC TEXT ===\n\n"
            "Find all inventory records in mtr_inventory_join_report that match this specification. "
            "Return all matching records as clickable cards."
        ) % (pdf_filename, spec_text)

        messages = [{"role": "user", "content": user_message}]

        answer, join_ids = _claude_agent_loop(env, messages, anthropic_key, anthropic_model, system_prompt)

        results = []
        if join_ids:
            report = env["mtr.inventory.join.report"]
            report_fields = _searchable_field_names(report)
            seen = set()
            for jid in join_ids:
                if jid in seen:
                    continue
                seen.add(jid)
                rows = report.search_read([("id", "=", jid)], fields=report_fields, limit=1)
                if rows:
                    row = rows[0]
                    row["join_id"] = row.get("id")
                    results.append(row)

        return request.make_response(
            json.dumps({"answer": answer, "results": results}, default=str),
            headers=[("Content-Type", "application/json")],
        )


def _build_spec_prompt(spec, branch=None):
    """Format a spec's structured requirements into a Claude prompt."""
    lines = ["SPECIFICATION: %s" % spec.name]
    if spec.customer:
        lines.append("Customer: %s" % spec.customer)

    targets = branch or spec.branch_ids[:1]
    branches_to_describe = [branch] if branch else list(spec.branch_ids)

    for b in branches_to_describe:
        lines.append("\n--- Branch: %s ---" % (b.name or b.branch_key or "Main"))
        if b.grades:
            lines.append("Accepted Grades: %s" % b.grades)
        if b.astm_equivalent:
            lines.append("ASTM Equivalents: %s" % b.astm_equivalent)
        if b.manufacturer_grades:
            lines.append("Manufacturer Grades: %s" % b.manufacturer_grades)
        if b.approved_substitutes:
            lines.append("Approved Substitutes: %s" % b.approved_substitutes)
        if b.selector_summary:
            lines.append("Selector Notes: %s" % b.selector_summary)

        # Chemistry limits
        chem_limits = b.branch_chem_limit_ids
        if chem_limits:
            lines.append("Chemistry Limits (element: min – max %):")
            for lim in chem_limits:
                parts = ["  %s:" % lim.element]
                if lim.min_value:
                    parts.append("min %.4f" % lim.min_value)
                if lim.max_value:
                    parts.append("max %.4f" % lim.max_value)
                lines.append(" ".join(parts))

        # Mechanical limits
        mech_limits = b.branch_mech_limit_ids
        if mech_limits:
            lines.append("Mechanical Limits:")
            for lim in mech_limits:
                prop = getattr(lim, "property_name", None) or getattr(lim, "target_element", None) or "?"
                parts = ["  %s:" % prop]
                if lim.min_value:
                    parts.append("min %.1f" % lim.min_value)
                if lim.max_value:
                    parts.append("max %.1f" % lim.max_value)
                lines.append(" ".join(parts))

        # Impact limits
        impact_limits = b.branch_impact_limit_ids
        if impact_limits:
            lines.append("Impact Limits:")
            for lim in impact_limits:
                lines.append("  Test temp: %s, Min avg: %s" % (
                    getattr(lim, "test_temp", "?"),
                    getattr(lim, "min_average", "?"),
                ))

        # CE thresholds
        ce_limits = b.branch_ce_threshold_ids
        if ce_limits:
            for ce in ce_limits:
                lines.append("CE Max: %s (formula: %s)" % (
                    getattr(ce, "max_value", "?"),
                    spec.ce_formula or "CE = C + Mn/6 + (Cr+Mo+V)/5 + (Ni+Cu)/15",
                ))

    return "\n".join(lines)


def _claude_spec_match_from_registry(env, spec, branch, api_key, model):
    """Use Claude + query_database to find all inventory matching the spec's structured requirements."""
    spec_prompt = _build_spec_prompt(spec, branch)

    system_prompt = (
        _CLAUDE_SYSTEM_PROMPT
        + "\n\nYou are matching Brannon Steel inventory against a customer specification. "
        "The spec requirements are provided below. "
        "Write SQL queries against mtr_inventory_join_report to find ALL records that qualify. "
        "Match on: (1) grade — check mtr_grade ILIKE against all accepted grades and equivalents; "
        "(2) chemistry — compare mtr_c, mtr_mn, mtr_si, mtr_p, mtr_s, mtr_cr, mtr_ni, mtr_mo, mtr_v, mtr_nb, mtr_al, mtr_ti, mtr_cu, mtr_b, mtr_n, mtr_ce columns against limits; "
        "(3) mechanical — compare mtr_yield_strength, mtr_tensile_strength, mtr_elongation, mtr_hardness columns against limits. "
        "Use LIMIT 500. Always include the id column. Filter WHERE join_status = 'Matched'. "
        "Return a summary: how many records pass, and what they are."
    )

    user_message = (
        "Find ALL inventory in mtr_inventory_join_report that qualifies for this specification.\n\n"
        "%s\n\n"
        "Query the database and return every matching record (use LIMIT 500). "
        "Show a count summary and list key details (batch, grade, dimensions, location)."
    ) % spec_prompt

    messages = [{"role": "user", "content": user_message}]
    return _claude_agent_loop(env, messages, api_key, model, system_prompt)


def _run_spec_match(env, spec_name=None, spec_id=None, branch_id=None):
    spec = None
    if spec_id:
        spec = env["mtr.specification"].search([("id", "=", spec_id)], limit=1)
    if not spec and spec_name:
        spec = env["mtr.specification"].search([("name", "ilike", spec_name)], limit=1)
    if not spec:
        return {
            "answer": _("Spec not found: %(name)s") % {"name": spec_name},
            "results": [],
        }

    branches = spec.branch_ids.sorted(lambda b: (b.sequence or 10, b.id))
    if branches and not branch_id:
        branch_lines = []
        for branch in branches:
            parts = [
                branch.name or branch.branch_key or "",
                branch.spec_type or "",
                branch.selector_summary or "",
            ]
            extra = []
            if branch.astm_equivalent:
                extra.append(_("ASTM: %s") % branch.astm_equivalent)
            if branch.grades:
                extra.append(_("Grades: %s") % branch.grades)
            if branch.manufacturer_grades:
                extra.append(_("Manufacturer: %s") % branch.manufacturer_grades)
            if branch.approved_substitutes:
                extra.append(_("Substitutes: %s") % branch.approved_substitutes)
            branch_lines.append({
                "id": branch.id,
                "name": branch.name,
                "branch_key": branch.branch_key,
                "spec_type": branch.spec_type,
                "selector_summary": branch.selector_summary,
                "astm_equivalent": branch.astm_equivalent,
                "grades": branch.grades,
                "manufacturer_grades": branch.manufacturer_grades,
                "approved_substitutes": branch.approved_substitutes,
                "display": " • ".join([p for p in parts if p]),
                "details": " | ".join(extra),
            })
        return {
            "answer": _("This spec has branches. Choose the one you want to match on:"),
            "need_branch": True,
            "spec_id": spec.id,
            "spec_name": spec.name,
            "branches": branch_lines,
            "results": [],
        }

    # Resolve branch record if branch_id supplied
    resolved_branch = None
    if branch_id:
        try:
            branch_id = int(branch_id)
        except Exception:
            branch_id = None
        if branch_id:
            resolved_branch = env["mtr.spec.rule.branch"].search(
                [("id", "=", branch_id), ("spec_id", "=", spec.id)], limit=1
            ) or None

    # Use Claude agentic loop when Anthropic key is configured
    params_cfg = env["ir.config_parameter"].sudo()
    anthropic_key = params_cfg.get_param("mtr_module.anthropic_api_key")
    if anthropic_key:
        anthropic_model = params_cfg.get_param("mtr_module.anthropic_model") or "claude-opus-4-5"
        answer, join_ids = _claude_spec_match_from_registry(
            env, spec, resolved_branch, anthropic_key, anthropic_model
        )
        rows = []
        if join_ids:
            report = env["mtr.inventory.join.report"]
            report_fields = _searchable_field_names(report)
            seen = set()
            for jid in join_ids:
                if jid in seen:
                    continue
                seen.add(jid)
                rec_rows = report.search_read([("id", "=", jid)], fields=report_fields, limit=1)
                if rec_rows:
                    row = rec_rows[0]
                    row["join_id"] = row.get("id")
                    rows.append(row)
        return {"answer": answer, "results": rows, "spec_id": spec.id, "spec_name": spec.name}

    # Fallback: Python matching engine
    wizard_vals = {"spec_id": spec.id}
    if resolved_branch:
        wizard_vals["branch_id"] = resolved_branch.id

    wizard = env["mtr.spec.match.wizard"].create(wizard_vals)
    try:
        wizard._run_match_engine(chem_only=False)
    except Exception as exc:
        msg = str(exc)
        if "No data to match" in msg:
            return {
                "answer": _("No inventory records are available to match."),
                "results": [],
            }
        return {
            "answer": _("No matches."),
            "results": [],
        }

    results = wizard.result_ids
    if not results:
        return {
            "answer": _("No matches."),
            "results": [],
        }

    rows = []
    join_report = env["mtr.inventory.join.report"]
    all_missing_notes = []
    for row in results:
        join = join_report.search([
            ("mtr_id", "=", row.mtr_id.id),
            ("inv_lot_number", "=", row.inventory_id.lot_number),
        ], limit=1)
        if row.missing_notes:
            all_missing_notes.extend([
                note.strip() for note in str(row.missing_notes).split(" | ")
                if note and note.strip()
            ])
        rows.append({
            "mtr_id": row.mtr_id.id,
            "inventory_id": row.inventory_id.id,
            "mtr_batch_number": row.mtr_id.batch_number,
            "mtr_heat_number": row.mtr_id.heat_number,
            "mtr_grade": row.mtr_id.grade,
            "matched_grade_label": row.matched_grade_label,
            "inv_lot_number": row.inventory_id.lot_number,
            "inv_heat_number": row.inventory_id.heat_number,
            "inv_item_no": row.inventory_id.item_no,
            "inv_dimensions": row.inventory_id.dimensions,
            "inv_weight": row.inventory_id.weight,
            "inv_location": row.inventory_id.location_code,
            "missing_notes": row.missing_notes,
            "chem_status": row.chem_status,
            "mech_status": row.mech_status,
            "impact_status": row.impact_status,
            "ce_status": row.ce_status,
            "grade_match": row.grade_match,
            "ce_value": row.ce_value,
            "ce_max": row.ce_max,
            "join_id": join.id if join else None,
        })

    params = env["ir.config_parameter"].sudo()
    top = results[:1]
    summary_lines = [
        _("Matches for %(spec)s: %(count)s") % {"spec": spec.name, "count": len(results)},
    ]
    if top:
        t = top[0]
        summary_lines.append(
            _("Top hit: %(batch)s / %(lot)s.") % {
                "batch": t.mtr_id.batch_number or t.mtr_id.heat_number or "",
                "lot": t.inventory_id.lot_number or "",
            }
        )
        matched_bits = []
        if getattr(t, "grade_match", False):
            matched_bits.append(
                _("Matched grade: %(label)s") % {
                    "label": t.matched_grade_label or (t.mtr_id.grade or ""),
                }
                if (t.matched_grade_label or t.mtr_id.grade)
                else _("Matched grade")
            )
        if getattr(t, "ce_value", None) is not None and getattr(t, "ce_max", None) is not None:
            matched_bits.append(_("CE %(ce)s <= %(max)s") % {
                "ce": t.ce_value,
                "max": t.ce_max,
            })
        if matched_bits:
            summary_lines.append(_("Matched checks: %s") % ", ".join(matched_bits))
    if all_missing_notes:
        unique_notes = []
        seen = set()
        for note in all_missing_notes:
            key = note.lower()
            if key not in seen:
                seen.add(key)
                unique_notes.append(note)
        summary_lines.append(_("Notes:"))
        summary_lines.extend(["- %s" % note for note in unique_notes[:8]])
        if len(unique_notes) > 8:
            summary_lines.append(_("... and %(count)s more") % {"count": len(unique_notes) - 8})
    answer = "\n".join(summary_lines)

    return {"answer": answer, "results": rows, "spec_id": spec.id, "spec_name": spec.name}


class MtrSpecIngestController(http.Controller):
    @http.route("/mtr_module/spec_ingest", type="json", auth="public", csrf=False)
    def spec_ingest(self, payload=None, token=None):
        env = request.env
        params = env["ir.config_parameter"].sudo()
        expected = params.get_param("mtr_module.spec_ingest_token") or ""
        raw_payload = payload

        # Fallback: accept raw JSON body (n8n can POST array/object without JSON-RPC)
        if not raw_payload:
            try:
                raw_body = request.httprequest.get_data(cache=False, as_text=True) or ""
                raw_body = raw_body.strip()
                if raw_body:
                    parsed = json.loads(raw_body)
                    # If JSON-RPC style, unwrap params.payload
                    if isinstance(parsed, dict) and "params" in parsed and isinstance(parsed.get("params"), dict):
                        raw_payload = parsed["params"].get("payload") or parsed["params"].get("data") or parsed["params"]
                    else:
                        raw_payload = parsed
            except Exception:
                raw_payload = None

        # If list of items, take the first (n8n often posts [ {..} ])
        if isinstance(raw_payload, list):
            raw_payload = raw_payload[0] if raw_payload else None

        provided = token or (raw_payload or {}).get("token") or ""
        if expected and provided != expected:
            return {"error": "invalid_token"}

        if not raw_payload:
            return {"error": "missing_payload"}
        if (raw_payload or {}).get("source") == "odoo13_mtr_module" and not (raw_payload or {}).get("spec_id"):
            return {
                "error": "missing_spec_id",
                "payload_keys": list((raw_payload or {}).keys()),
            }

        spec = env["mtr.specification"].sudo().upsert_from_payload(raw_payload)
        return {"status": "ok", "spec_id": spec.get("id")}
