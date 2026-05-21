DO $$
DECLARE
    v_spec_id int;
    v_branch_id int;
BEGIN
    DELETE FROM mtr_spec_chem_limit WHERE spec_id IN (SELECT id FROM mtr_specification WHERE name = 'DEMO UNIT CONVERSION');
    DELETE FROM mtr_spec_mech_limit WHERE spec_id IN (SELECT id FROM mtr_specification WHERE name = 'DEMO UNIT CONVERSION');
    DELETE FROM mtr_spec_impact_limit WHERE spec_id IN (SELECT id FROM mtr_specification WHERE name = 'DEMO UNIT CONVERSION');
    DELETE FROM mtr_spec_condition_rule WHERE spec_id IN (SELECT id FROM mtr_specification WHERE name = 'DEMO UNIT CONVERSION');
    DELETE FROM mtr_spec_ce_threshold WHERE spec_id IN (SELECT id FROM mtr_specification WHERE name = 'DEMO UNIT CONVERSION');
    DELETE FROM mtr_spec_rule_branch WHERE spec_id IN (SELECT id FROM mtr_specification WHERE name = 'DEMO UNIT CONVERSION');
    DELETE FROM mtr_specification WHERE name = 'DEMO UNIT CONVERSION';
    DELETE FROM inventory WHERE lot_number = 'DEMO-LOT-1';
    DELETE FROM mtr_data WHERE batch_number = 'DEMO-BATCH-1' AND certificate_number = 'DEMO-CERT-1';

    INSERT INTO mtr_specification (name, customer, status, ce_formula, notes)
    VALUES (
        'DEMO UNIT CONVERSION',
        'CATERPILLAR',
        'active',
        'CE = C + Mn/6 + (Cr+Mo+V)/5 + (Ni+Cu)/15',
        'Demo spec for unit-conversion testing'
    )
    RETURNING id INTO v_spec_id;

    INSERT INTO mtr_spec_rule_branch (
        spec_id,
        branch_key,
        name,
        selector_summary,
        spec_type,
        ai_summary,
        astm_equivalent,
        grades,
        manufacturer_grades,
        approved_substitutes,
        notes,
        selector_json,
        branch_json,
        sequence
    )
    VALUES (
        v_spec_id,
        'thickness_to_65mm_inclusive',
        'Thickness to 65mm Inclusive',
        'Thickness to 65mm inclusive',
        'steel',
        'Demo branch for unit conversion',
        '1E0577',
        '1E0577',
        '1E0577',
        '',
        'Demo branch',
        '{"field":"thickness","operator":"<=","value":65,"unit":"mm"}',
        '{"branch_key":"thickness_to_65mm_inclusive","name":"Thickness to 65mm Inclusive","selector_summary":"Thickness to 65mm inclusive","spec_type":"steel","product_forms":[{"form":"plate","thickness_min":0,"thickness_max":65,"thickness_unit":"mm","description":"Demo plate branch"}],"chem_limits":[{"element":"c","max":0.2,"unit":"%","source_unit":"%"}],"mech_limits":[{"property":"yield","min":62000,"unit":"psi","specimen_size":"1E0552 X6/X9 (<22mm), X1/X2 (>=22mm)","source_unit":"psi"},{"property":"tensile","min":69000,"unit":"psi","specimen_size":"1E0552 X6/X9 (<22mm), X1/X2 (>=22mm)","source_unit":"psi"},{"property":"elongation","min":22,"unit":"%","specimen_size":"1E0552 X6/X9 (<22mm), X1/X2 (>=22mm)"}],"impact_limits":[{"temperature":-22,"temperature_unit":"f","coupon_size":"A","min_average":21,"min_individual":11,"unit":"j","min_readings":3,"orientation":"longitudinal"}],"ce_thresholds":[]}',
        1
    )
    RETURNING id INTO v_branch_id;

    INSERT INTO mtr_spec_chem_limit (spec_id, branch_id, element, max_value, source)
    VALUES
        (v_spec_id, v_branch_id, 'c', 0.20, 'table'),
        (v_spec_id, v_branch_id, 'mn', 1.60, 'table'),
        (v_spec_id, v_branch_id, 'p', 0.035, 'table'),
        (v_spec_id, v_branch_id, 's', 0.020, 'table'),
        (v_spec_id, v_branch_id, 'si', 0.50, 'table');

    INSERT INTO mtr_spec_mech_limit (spec_id, branch_id, property, min_value, unit, specimen_size)
    VALUES
        (v_spec_id, v_branch_id, 'yield', 62000, 'psi', '1E0552 X6/X9 (<22mm), X1/X2 (>=22mm)'),
        (v_spec_id, v_branch_id, 'tensile', 69000, 'psi', '1E0552 X6/X9 (<22mm), X1/X2 (>=22mm)'),
        (v_spec_id, v_branch_id, 'elongation', 22, '%', '1E0552 X6/X9 (<22mm), X1/X2 (>=22mm)');

    INSERT INTO mtr_spec_impact_limit (spec_id, branch_id, temperature, coupon_size, min_average, min_individual, unit, min_readings, orientation)
    VALUES
        (v_spec_id, v_branch_id, -22, 'A', 21, 11, 'j', 3, 'longitudinal');

    INSERT INTO inventory (lot_number, heat_number, slab_number, item_no, dimensions, quantity, description, document_no, grade, image_path, weight, source_file)
    VALUES
        ('DEMO-LOT-1', 'DEMO-HEAT-1', 'DEMO-BATCH-1', 'DEMO-ITEM-1', '1.0 x 48 x 120', 100, 'Demo plate', 'DEMO-DOC-1', '1E0577', 'DEMO-CERT-1', 1000, 'demo_unit_conversion.csv');

    INSERT INTO mtr_data (
        batch_number,
        heat_number,
        certificate_number,
        grade,
        manufacturer,
        c_element,
        mn_element,
        si_element,
        p_element,
        s_element,
        yield_strength,
        tensile_strength,
        elongation,
        hardness,
        impact_test_temp,
        impact_coupon_size,
        impact_specimen_1,
        impact_specimen_2,
        impact_specimen_3,
        impact_average,
        thickness,
        plate_dimension,
        direction,
        country_of_melt,
        country_of_manufacture
    )
    VALUES (
        'DEMO-BATCH-1',
        'DEMO-HEAT-1',
        'DEMO-CERT-1',
        '1E0577',
        'Demo Mill',
        0.18,
        1.20,
        0.30,
        0.015,
        0.008,
        69000,
        75000,
        24,
        180,
        -22,
        'A',
        24,
        23,
        22,
        23,
        1.0,
        '1.0 x 48 x 120',
        'Longitudinal',
        'USA',
        'USA'
    );

    RAISE NOTICE 'seeded spec_id=%, branch_id=%', v_spec_id, v_branch_id;

    DELETE FROM mtr_spec_chem_limit WHERE spec_id IN (SELECT id FROM mtr_specification WHERE name = 'DEMO LW1020A PIPE');
    DELETE FROM mtr_spec_mech_limit WHERE spec_id IN (SELECT id FROM mtr_specification WHERE name = 'DEMO LW1020A PIPE');
    DELETE FROM mtr_spec_impact_limit WHERE spec_id IN (SELECT id FROM mtr_specification WHERE name = 'DEMO LW1020A PIPE');
    DELETE FROM mtr_spec_condition_rule WHERE spec_id IN (SELECT id FROM mtr_specification WHERE name = 'DEMO LW1020A PIPE');
    DELETE FROM mtr_spec_ce_threshold WHERE spec_id IN (SELECT id FROM mtr_specification WHERE name = 'DEMO LW1020A PIPE');
    DELETE FROM mtr_spec_rule_branch WHERE spec_id IN (SELECT id FROM mtr_specification WHERE name = 'DEMO LW1020A PIPE');
    DELETE FROM mtr_specification WHERE name = 'DEMO LW1020A PIPE';
    DELETE FROM inventory WHERE lot_number = 'LW1020A-LOT-1';
    DELETE FROM mtr_data WHERE batch_number = 'LW1020A-BATCH-1' AND certificate_number = 'LW1020A-CERT-1';

    DELETE FROM mtr_spec_chem_limit WHERE spec_id IN (SELECT id FROM mtr_specification WHERE name = 'DEMO FULL FIELD STRESS');
    DELETE FROM mtr_spec_mech_limit WHERE spec_id IN (SELECT id FROM mtr_specification WHERE name = 'DEMO FULL FIELD STRESS');
    DELETE FROM mtr_spec_impact_limit WHERE spec_id IN (SELECT id FROM mtr_specification WHERE name = 'DEMO FULL FIELD STRESS');
    DELETE FROM mtr_spec_condition_rule WHERE spec_id IN (SELECT id FROM mtr_specification WHERE name = 'DEMO FULL FIELD STRESS');
    DELETE FROM mtr_spec_ce_threshold WHERE spec_id IN (SELECT id FROM mtr_specification WHERE name = 'DEMO FULL FIELD STRESS');
    DELETE FROM mtr_spec_custom_rule WHERE spec_id IN (SELECT id FROM mtr_specification WHERE name = 'DEMO FULL FIELD STRESS');
    DELETE FROM mtr_spec_rule_branch WHERE spec_id IN (SELECT id FROM mtr_specification WHERE name = 'DEMO FULL FIELD STRESS');
    DELETE FROM mtr_specification WHERE name = 'DEMO FULL FIELD STRESS';
    DELETE FROM inventory WHERE lot_number IN ('STRESS-LOT-1', 'STRESS-LOT-2');
    DELETE FROM mtr_data WHERE batch_number IN ('STRESS-BATCH-1', 'STRESS-BATCH-2')
        AND certificate_number IN ('STRESS-CERT-1', 'STRESS-CERT-2');

    INSERT INTO mtr_specification (name, customer, status, ce_formula, notes)
    VALUES (
        'DEMO LW1020A PIPE',
        'KOMATSU',
        'active',
        'CE = C + Mn/6 + (Cr+Mo+V)/5 + (Ni+Cu)/15',
        'Demo spec for LW1020A grade matching'
    )
    RETURNING id INTO v_spec_id;

    INSERT INTO mtr_spec_rule_branch (
        spec_id,
        branch_key,
        name,
        selector_summary,
        spec_type,
        ai_summary,
        astm_equivalent,
        grades,
        manufacturer_grades,
        approved_substitutes,
        notes,
        selector_json,
        branch_json,
        sequence
    )
    VALUES (
        v_spec_id,
        'pipe',
        'Pipe',
        'Pipe',
        'mild_steel',
        'Demo branch for LW1020A grade matching',
        'A53',
        'M1008, M1009, M1010, M1012, M1015, M1016, M1017, M1018, M1019, M1020, M1021, M1022, M1025, 1008, 1009, 1010, 1012, 1015, 1016, 1017, 1018, 1019, 1020, 1021, 1022, 1026',
        '',
        'LW1020A',
        'Demo pipe branch for LW1020A',
        '{"field":"grade","operator":"in","value":["A53","LW1020A"]}',
        '{"branch_key":"pipe","name":"Pipe","selector_summary":"Pipe","spec_type":"mild_steel","product_forms":[{"form":"pipe","thickness_min":0,"thickness_max":999,"thickness_unit":"in","description":"Demo pipe branch"}],"chem_limits":[],"mech_limits":[],"impact_limits":[],"condition_rules":[],"ce_thresholds":[],"custom_rules":[]}',
        1
    )
    RETURNING id INTO v_branch_id;

    INSERT INTO inventory (lot_number, heat_number, slab_number, item_no, dimensions, quantity, description, document_no, grade, image_path, weight, source_file)
    VALUES (
        'LW1020A-LOT-1',
        'LW1020A-BATCH-1',
        'LW1020A-BATCH-1',
        'LW1020A-ITEM-1',
        '1.0 x 24 x 120',
        50,
        'LW1020A pipe inventory',
        'LW1020A-DOC-1',
        'LW1020A',
        'LW1020A-CERT-1',
        500,
        'demo_lw1020a_pipe.csv'
    );

    INSERT INTO mtr_data (
        batch_number,
        heat_number,
        certificate_number,
        grade,
        manufacturer,
        c_element,
        mn_element,
        si_element,
        p_element,
        s_element,
        yield_strength,
        tensile_strength,
        elongation,
        hardness,
        thickness,
        plate_dimension,
        direction,
        country_of_melt,
        country_of_manufacture
    )
    VALUES (
        'LW1020A-BATCH-1',
        'LW1020A-HEAT-1',
        'LW1020A-CERT-1',
        'LW1020A',
        'Demo Mill',
        0.08,
        0.40,
        0.02,
        0.010,
        0.005,
        29000,
        46000,
        30,
        120,
        1.0,
        '1.0 x 24 x 120',
        'Longitudinal',
        'USA',
        'USA'
    );

    RAISE NOTICE 'seeded LW1020A demo spec_id=%, branch_id=%', v_spec_id, v_branch_id;

    INSERT INTO mtr_specification (name, customer, status, ce_formula, notes)
    VALUES (
        'DEMO FULL FIELD STRESS',
        'CATERPILLAR',
        'active',
        'CE = C + Mn/6 + (Cr+Mo+V)/5 + (Ni+Cu)/15',
        'Stress test spec covering chemistry, mechanics, impact, CE, thickness, custom rule, and join matching'
    )
    RETURNING id INTO v_spec_id;

    INSERT INTO mtr_spec_rule_branch (
        spec_id,
        branch_key,
        name,
        selector_summary,
        spec_type,
        ai_summary,
        astm_equivalent,
        grades,
        manufacturer_grades,
        approved_substitutes,
        notes,
        selector_json,
        branch_json,
        sequence
    )
    VALUES (
        v_spec_id,
        'plate_up_to_2_in',
        'Plate up to 2.00 inches Stress',
        'Plate thickness up to 2.00 inches',
        'plate',
        'Full field stress branch for plates up to 2.00 inches',
        'A514',
        'STRESSGRADE',
        'Demo Mill',
        'A514 Grades B, H, S, 700Q',
        'Stress branch for 0 to 2 inches',
        '{"field":"thickness","operator":"<=","value":2.0,"unit":"in"}',
        '{"branch_key":"plate_up_to_2_in","name":"Plate up to 2.00 inches Stress","selector_summary":"Plate thickness up to 2.00 inches","spec_type":"plate","product_forms":[{"form":"plate","thickness_min":0,"thickness_max":2.0,"thickness_unit":"in","description":"Stress test plate branch up to 2 inches"}],"chem_limits":[{"element":"c","max":0.20,"unit":"%","source_unit":"%"},{"element":"mn","max":1.50,"unit":"%","source_unit":"%"},{"element":"si","max":0.50,"unit":"%","source_unit":"%"},{"element":"p","max":0.020,"unit":"%","source_unit":"%"},{"element":"s","max":0.015,"unit":"%","source_unit":"%"},{"element":"cu","max":0.15,"unit":"%","source_unit":"%"},{"element":"ni","max":0.15,"unit":"%","source_unit":"%"},{"element":"cr","max":0.15,"unit":"%","source_unit":"%"},{"element":"mo","max":0.05,"unit":"%","source_unit":"%"},{"element":"b","max":0.003,"unit":"%","source_unit":"%"},{"element":"nb","max":0.05,"unit":"%","source_unit":"%"},{"element":"ti","max":0.03,"unit":"%","source_unit":"%"},{"element":"v","max":0.08,"unit":"%","source_unit":"%"}],"mech_limits":[{"property":"yield","min":62000,"unit":"psi","specimen_size":"X1/X2","direction":"longitudinal","source_unit":"psi"},{"property":"tensile","min":69000,"unit":"psi","specimen_size":"X1/X2","direction":"longitudinal","source_unit":"psi"},{"property":"elongation","min":22,"unit":"%","specimen_size":"X1/X2","direction":"longitudinal"},{"property":"hardness","min":140,"max":220,"unit":"HBW","specimen_size":"","direction":"longitudinal","source_unit":"HBW"}],"impact_limits":[{"temperature":-40,"temperature_unit":"f","coupon_size":"A","min_average":20,"min_individual":10,"unit":"ft-lbf","min_readings":3,"orientation":"longitudinal","source_unit":"ft-lbf"}],"condition_rules":[{"target_element":"c","condition_element":"mn","condition_type":"above","condition_threshold":1.0,"target_adjustment":0.0,"target_new_max":0.20,"description":"If Mn is above 1.0, cap C at 0.20"}],"ce_thresholds":[{"thickness_min":0,"thickness_max":2.0,"thickness_unit":"in","max_ce":0.45,"applies_to_forms":["plate"],"applies_to_grades":["STRESSGRADE"]}],"custom_rules":[{"rule_type":"quality","label":"Manufacturer must be Demo Mill","field_name":"manufacturer","operator":"contains","value_text":"Demo Mill","value_number":null,"value_unit":"","description":"Manufacturer should contain Demo Mill"}],"notes":"Branch 1 stress test"}',
        1
    )
    RETURNING id INTO v_branch_id;

    INSERT INTO mtr_spec_chem_limit (spec_id, branch_id, element, max_value, source)
    VALUES
        (v_spec_id, v_branch_id, 'c', 0.20, 'table'),
        (v_spec_id, v_branch_id, 'mn', 1.50, 'table'),
        (v_spec_id, v_branch_id, 'si', 0.50, 'table'),
        (v_spec_id, v_branch_id, 'p', 0.020, 'table'),
        (v_spec_id, v_branch_id, 's', 0.015, 'table'),
        (v_spec_id, v_branch_id, 'cu', 0.15, 'table'),
        (v_spec_id, v_branch_id, 'ni', 0.15, 'table'),
        (v_spec_id, v_branch_id, 'cr', 0.15, 'table'),
        (v_spec_id, v_branch_id, 'mo', 0.05, 'table'),
        (v_spec_id, v_branch_id, 'b', 0.003, 'table'),
        (v_spec_id, v_branch_id, 'nb', 0.05, 'table'),
        (v_spec_id, v_branch_id, 'ti', 0.03, 'table'),
        (v_spec_id, v_branch_id, 'v', 0.08, 'table');

    INSERT INTO mtr_spec_mech_limit (spec_id, branch_id, property, min_value, max_value, unit, specimen_size)
    VALUES
        (v_spec_id, v_branch_id, 'yield', 62000, NULL, 'psi', 'X1/X2'),
        (v_spec_id, v_branch_id, 'tensile', 69000, NULL, 'psi', 'X1/X2'),
        (v_spec_id, v_branch_id, 'elongation', 22, NULL, '%', 'X1/X2'),
        (v_spec_id, v_branch_id, 'hardness', 140, 220, 'HBW', '');

    INSERT INTO mtr_spec_impact_limit (spec_id, branch_id, temperature, coupon_size, min_average, min_individual, unit, min_readings, orientation)
    VALUES
        (v_spec_id, v_branch_id, -40, 'A', 20, 10, 'ft-lbf', 3, 'longitudinal');

    INSERT INTO mtr_spec_condition_rule (spec_id, branch_id, target_element, condition_element, condition_type, condition_threshold, target_adjustment, target_new_max, description)
    VALUES
        (v_spec_id, v_branch_id, 'c', 'mn', 'above', 1.0, 0.0, 0.20, 'If Mn is above 1.0, cap C at 0.20');

    INSERT INTO mtr_spec_ce_threshold (spec_id, branch_id, thickness_min, thickness_max, max_ce)
    VALUES
        (v_spec_id, v_branch_id, 0.0, 2.0, 0.45);

    INSERT INTO mtr_spec_custom_rule (spec_id, branch_id, rule_type, label, field_name, operator, value_text, value_number, value_unit, description, raw_json)
    VALUES (
        v_spec_id,
        v_branch_id,
        'quality',
        'Manufacturer must be Demo Mill',
        'manufacturer',
        'contains',
        'Demo Mill',
        NULL,
        '',
        'Manufacturer should contain Demo Mill',
        '{"rule_type":"quality","label":"Manufacturer must be Demo Mill","field_name":"manufacturer","operator":"contains","value_text":"Demo Mill"}'
    );

    INSERT INTO mtr_spec_rule_branch (
        spec_id,
        branch_key,
        name,
        selector_summary,
        spec_type,
        ai_summary,
        astm_equivalent,
        grades,
        manufacturer_grades,
        approved_substitutes,
        notes,
        selector_json,
        branch_json,
        sequence
    )
    VALUES (
        v_spec_id,
        'plate_2_to_4_in',
        'Plate 2.00 to 4.00 inches Stress',
        'Plate thickness over 2.00 inches to 4.00 inches',
        'plate',
        'Full field stress branch for plates over 2.00 inches to 4.00 inches',
        'A514',
        'STRESSGRADE',
        'Demo Mill',
        'A514 Grades B, H, S, 700Q',
        'Stress branch for 2 to 4 inches',
        '{"field":"thickness","operator":">","value":2.0,"unit":"in"}',
        '{"branch_key":"plate_2_to_4_in","name":"Plate 2.00 to 4.00 inches Stress","selector_summary":"Plate thickness over 2.00 inches to 4.00 inches","spec_type":"plate","product_forms":[{"form":"plate","thickness_min":2.0,"thickness_max":4.0,"thickness_unit":"in","description":"Stress test plate branch over 2 to 4 inches"}],"chem_limits":[{"element":"c","max":0.20,"unit":"%","source_unit":"%"},{"element":"mn","max":1.50,"unit":"%","source_unit":"%"},{"element":"si","max":0.50,"unit":"%","source_unit":"%"},{"element":"p","max":0.020,"unit":"%","source_unit":"%"},{"element":"s","max":0.015,"unit":"%","source_unit":"%"},{"element":"cu","max":0.15,"unit":"%","source_unit":"%"},{"element":"ni","max":0.15,"unit":"%","source_unit":"%"},{"element":"cr","max":0.15,"unit":"%","source_unit":"%"},{"element":"mo","max":0.05,"unit":"%","source_unit":"%"},{"element":"b","max":0.003,"unit":"%","source_unit":"%"},{"element":"nb","max":0.05,"unit":"%","source_unit":"%"},{"element":"ti","max":0.03,"unit":"%","source_unit":"%"},{"element":"v","max":0.08,"unit":"%","source_unit":"%"}],"mech_limits":[{"property":"yield","min":62000,"unit":"psi","specimen_size":"X1/X2","direction":"longitudinal","source_unit":"psi"},{"property":"tensile","min":69000,"unit":"psi","specimen_size":"X1/X2","direction":"longitudinal","source_unit":"psi"},{"property":"elongation","min":22,"unit":"%","specimen_size":"X1/X2","direction":"longitudinal"},{"property":"hardness","min":140,"max":220,"unit":"HBW","specimen_size":"","direction":"longitudinal","source_unit":"HBW"}],"impact_limits":[{"temperature":-40,"temperature_unit":"f","coupon_size":"A","min_average":20,"min_individual":10,"unit":"ft-lbf","min_readings":3,"orientation":"longitudinal","source_unit":"ft-lbf"}],"condition_rules":[{"target_element":"c","condition_element":"mn","condition_type":"above","condition_threshold":1.0,"target_adjustment":0.0,"target_new_max":0.20,"description":"If Mn is above 1.0, cap C at 0.20"}],"ce_thresholds":[{"thickness_min":2.0,"thickness_max":4.0,"thickness_unit":"in","max_ce":0.45,"applies_to_forms":["plate"],"applies_to_grades":["STRESSGRADE"]}],"custom_rules":[{"rule_type":"quality","label":"Manufacturer must be Demo Mill","field_name":"manufacturer","operator":"contains","value_text":"Demo Mill","value_number":null,"value_unit":"","description":"Manufacturer should contain Demo Mill"}],"notes":"Branch 2 stress test"}',
        2
    )
    RETURNING id INTO v_branch_id;

    INSERT INTO mtr_spec_chem_limit (spec_id, branch_id, element, max_value, source)
    VALUES
        (v_spec_id, v_branch_id, 'c', 0.20, 'table'),
        (v_spec_id, v_branch_id, 'mn', 1.50, 'table'),
        (v_spec_id, v_branch_id, 'si', 0.50, 'table'),
        (v_spec_id, v_branch_id, 'p', 0.020, 'table'),
        (v_spec_id, v_branch_id, 's', 0.015, 'table'),
        (v_spec_id, v_branch_id, 'cu', 0.15, 'table'),
        (v_spec_id, v_branch_id, 'ni', 0.15, 'table'),
        (v_spec_id, v_branch_id, 'cr', 0.15, 'table'),
        (v_spec_id, v_branch_id, 'mo', 0.05, 'table'),
        (v_spec_id, v_branch_id, 'b', 0.003, 'table'),
        (v_spec_id, v_branch_id, 'nb', 0.05, 'table'),
        (v_spec_id, v_branch_id, 'ti', 0.03, 'table'),
        (v_spec_id, v_branch_id, 'v', 0.08, 'table');

    INSERT INTO mtr_spec_mech_limit (spec_id, branch_id, property, min_value, max_value, unit, specimen_size)
    VALUES
        (v_spec_id, v_branch_id, 'yield', 62000, NULL, 'psi', 'X1/X2'),
        (v_spec_id, v_branch_id, 'tensile', 69000, NULL, 'psi', 'X1/X2'),
        (v_spec_id, v_branch_id, 'elongation', 22, NULL, '%', 'X1/X2'),
        (v_spec_id, v_branch_id, 'hardness', 140, 220, 'HBW', '');

    INSERT INTO mtr_spec_impact_limit (spec_id, branch_id, temperature, coupon_size, min_average, min_individual, unit, min_readings, orientation)
    VALUES
        (v_spec_id, v_branch_id, -40, 'A', 20, 10, 'ft-lbf', 3, 'longitudinal');

    INSERT INTO mtr_spec_condition_rule (spec_id, branch_id, target_element, condition_element, condition_type, condition_threshold, target_adjustment, target_new_max, description)
    VALUES
        (v_spec_id, v_branch_id, 'c', 'mn', 'above', 1.0, 0.0, 0.20, 'If Mn is above 1.0, cap C at 0.20');

    INSERT INTO mtr_spec_ce_threshold (spec_id, branch_id, thickness_min, thickness_max, max_ce)
    VALUES
        (v_spec_id, v_branch_id, 2.0, 4.0, 0.45);

    INSERT INTO mtr_spec_custom_rule (spec_id, branch_id, rule_type, label, field_name, operator, value_text, value_number, value_unit, description, raw_json)
    VALUES (
        v_spec_id,
        v_branch_id,
        'quality',
        'Manufacturer must be Demo Mill',
        'manufacturer',
        'contains',
        'Demo Mill',
        NULL,
        '',
        'Manufacturer should contain Demo Mill',
        '{"rule_type":"quality","label":"Manufacturer must be Demo Mill","field_name":"manufacturer","operator":"contains","value_text":"Demo Mill"}'
    );

    INSERT INTO inventory (lot_number, heat_number, slab_number, item_no, dimensions, quantity, description, document_no, grade, image_path, weight, source_file)
    VALUES
        ('STRESS-LOT-1', 'STRESS-HEAT-1', 'STRESS-BATCH-1', 'STRESS-ITEM-1', '1.50 x 48 x 120', 120, 'Stress plate inventory 1', 'STRESS-DOC-1', 'STRESSGRADE', 'STRESS-CERT-1', 1400, 'demo_full_field_stress_1.csv'),
        ('STRESS-LOT-2', 'STRESS-HEAT-2', 'STRESS-BATCH-2', 'STRESS-ITEM-2', '3.00 x 48 x 120', 140, 'Stress plate inventory 2', 'STRESS-DOC-2', 'STRESSGRADE', 'STRESS-CERT-2', 1800, 'demo_full_field_stress_2.csv');

    INSERT INTO mtr_data (
        batch_number,
        heat_number,
        certificate_number,
        grade,
        manufacturer,
        c_element,
        mn_element,
        si_element,
        p_element,
        s_element,
        b_element,
        v_element,
        nb_element,
        ti_element,
        al_element,
        ca_element,
        zr_element,
        zn_element,
        sn_element,
        cu_element,
        ni_element,
        cr_element,
        mo_element,
        n_element,
        yield_strength,
        tensile_strength,
        elongation,
        hardness,
        impact_test_temp,
        impact_coupon_size,
        impact_specimen_1,
        impact_specimen_2,
        impact_specimen_3,
        impact_average,
        thickness,
        plate_dimension,
        direction,
        country_of_melt,
        country_of_manufacture
    )
    VALUES
    (
        'STRESS-BATCH-1',
        'STRESS-HEAT-1',
        'STRESS-CERT-1',
        'STRESSGRADE',
        'Demo Mill',
        0.16,
        1.25,
        0.30,
        0.015,
        0.006,
        0.0004,
        0.0600,
        0.0300,
        0.0200,
        0.0300,
        0.0020,
        0.0010,
        0.0010,
        0.0010,
        0.1000,
        0.1200,
        0.1400,
        0.0300,
        0.0040,
        70000,
        80000,
        24,
        180,
        -50,
        'A',
        24,
        25,
        23,
        24,
        1.50,
        '1.50 x 48 x 120',
        'Longitudinal',
        'USA',
        'USA'
    ),
    (
        'STRESS-BATCH-2',
        'STRESS-HEAT-2',
        'STRESS-CERT-2',
        'STRESSGRADE',
        'Demo Mill',
        0.16,
        1.25,
        0.30,
        0.015,
        0.006,
        0.0004,
        0.0600,
        0.0300,
        0.0200,
        0.0300,
        0.0020,
        0.0010,
        0.0010,
        0.0010,
        0.1000,
        0.1200,
        0.1400,
        0.0300,
        0.0040,
        70000,
        80000,
        24,
        180,
        -50,
        'A',
        24,
        25,
        23,
        24,
        3.00,
        '3.00 x 48 x 120',
        'Longitudinal',
        'USA',
        'USA'
    );

    RAISE NOTICE 'seeded FULL FIELD STRESS demo spec_id=%, branch_id=%', v_spec_id, v_branch_id;

    DELETE FROM mtr_spec_chem_limit WHERE spec_id IN (SELECT id FROM mtr_specification WHERE name = 'DEMO MATCH COVERAGE LAB');
    DELETE FROM mtr_spec_mech_limit WHERE spec_id IN (SELECT id FROM mtr_specification WHERE name = 'DEMO MATCH COVERAGE LAB');
    DELETE FROM mtr_spec_impact_limit WHERE spec_id IN (SELECT id FROM mtr_specification WHERE name = 'DEMO MATCH COVERAGE LAB');
    DELETE FROM mtr_spec_condition_rule WHERE spec_id IN (SELECT id FROM mtr_specification WHERE name = 'DEMO MATCH COVERAGE LAB');
    DELETE FROM mtr_spec_ce_threshold WHERE spec_id IN (SELECT id FROM mtr_specification WHERE name = 'DEMO MATCH COVERAGE LAB');
    DELETE FROM mtr_spec_custom_rule WHERE spec_id IN (SELECT id FROM mtr_specification WHERE name = 'DEMO MATCH COVERAGE LAB');
    DELETE FROM mtr_spec_rule_branch WHERE spec_id IN (SELECT id FROM mtr_specification WHERE name = 'DEMO MATCH COVERAGE LAB');
    DELETE FROM mtr_specification WHERE name = 'DEMO MATCH COVERAGE LAB';
    DELETE FROM inventory WHERE lot_number IN (
        'COV-LOT-PASS-LOT',
        'COV-LOT-PASS-HEAT',
        'COV-LOT-PASS-SLAB',
        'COV-LOT-PASS-CERT',
        'COV-LOT-FAIL-CHEM',
        'COV-LOT-FAIL-MECH',
        'COV-LOT-FAIL-IMPACT',
        'COV-LOT-FAIL-CE',
        'COV-LOT-FAIL-CUSTOM',
        'COV-LOT-PASS-MM'
    );
    DELETE FROM mtr_data WHERE batch_number IN (
        'COV-BATCH-PASS',
        'COV-BATCH-FAIL-CHEM',
        'COV-BATCH-FAIL-MECH',
        'COV-BATCH-FAIL-IMPACT',
        'COV-BATCH-FAIL-CE',
        'COV-BATCH-FAIL-CUSTOM',
        'COV-BATCH-PASS-MM'
    ) AND certificate_number IN (
        'COV-CERT-PASS',
        'COV-CERT-FAIL-CHEM',
        'COV-CERT-FAIL-MECH',
        'COV-CERT-FAIL-IMPACT',
        'COV-CERT-FAIL-CE',
        'COV-CERT-FAIL-CUSTOM',
        'COV-CERT-PASS-MM'
    );

    INSERT INTO mtr_specification (name, customer, status, ce_formula, notes)
    VALUES (
        'DEMO MATCH COVERAGE LAB',
        'CATERPILLAR',
        'active',
        'CE = C + Mn/6 + (Cr+Mo+V)/5 + (Ni+Cu)/15',
        'Demo lab with pass and fail records for every major spec-matching path'
    )
    RETURNING id INTO v_spec_id;

    INSERT INTO mtr_spec_rule_branch (
        spec_id,
        branch_key,
        name,
        selector_summary,
        spec_type,
        ai_summary,
        astm_equivalent,
        grades,
        manufacturer_grades,
        approved_substitutes,
        notes,
        selector_json,
        branch_json,
        sequence
    )
    VALUES (
        v_spec_id,
        'all_checks',
        'All Checks Coverage',
        'Chemistry, mechanics, impact, CE, and custom-rule coverage',
        'plate',
        'Coverage branch for testing every match path',
        'COVGRADE',
        'COVGRADE',
        'Demo Mill',
        '',
        'Coverage branch',
        '{"field":"grade","operator":"=","value":"COVGRADE"}',
        '{"branch_key":"all_checks","name":"All Checks Coverage","selector_summary":"Chemistry, mechanics, impact, CE, and custom-rule coverage","spec_type":"plate","product_forms":[{"form":"plate","thickness_min":0,"thickness_max":4.0,"thickness_unit":"in","description":"Coverage branch for plate matching"}],"chem_limits":[{"element":"c","max":0.20,"unit":"%","source_unit":"%"},{"element":"mn","max":1.50,"unit":"%","source_unit":"%"},{"element":"si","max":0.50,"unit":"%","source_unit":"%"},{"element":"p","max":0.020,"unit":"%","source_unit":"%"},{"element":"s","max":0.015,"unit":"%","source_unit":"%"},{"element":"cu","max":0.15,"unit":"%","source_unit":"%"},{"element":"ni","max":0.15,"unit":"%","source_unit":"%"},{"element":"cr","max":0.15,"unit":"%","source_unit":"%"},{"element":"mo","max":0.05,"unit":"%","source_unit":"%"},{"element":"b","max":0.003,"unit":"%","source_unit":"%"},{"element":"nb","max":0.05,"unit":"%","source_unit":"%"},{"element":"ti","max":0.03,"unit":"%","source_unit":"%"},{"element":"v","max":0.08,"unit":"%","source_unit":"%"}],"mech_limits":[{"property":"yield","min":62000,"unit":"psi","specimen_size":"X1/X2","direction":"longitudinal","source_unit":"psi"},{"property":"tensile","min":69000,"unit":"psi","specimen_size":"X1/X2","direction":"longitudinal","source_unit":"psi"},{"property":"elongation","min":22,"unit":"%","specimen_size":"X1/X2","direction":"longitudinal"},{"property":"hardness","min":140,"max":220,"unit":"HBW","specimen_size":"","direction":"longitudinal","source_unit":"HBW"}],"impact_limits":[{"temperature":-40,"temperature_unit":"f","coupon_size":"A","min_average":20,"min_individual":10,"unit":"ft-lbf","min_readings":3,"orientation":"longitudinal","source_unit":"ft-lbf"}],"condition_rules":[{"target_element":"c","condition_element":"mn","condition_type":"above","condition_threshold":1.0,"target_adjustment":0.0,"target_new_max":0.20,"description":"If Mn is above 1.0, cap C at 0.20"}],"ce_thresholds":[{"thickness_min":0,"thickness_max":4.0,"thickness_unit":"in","max_ce":0.45,"applies_to_forms":["plate"],"applies_to_grades":["COVGRADE"]}],"custom_rules":[{"rule_type":"quality","label":"Manufacturer must contain Demo Mill","field_name":"manufacturer","operator":"contains","value_text":"Demo Mill","value_number":null,"value_unit":"","description":"Manufacturer should contain Demo Mill"}],"notes":"Coverage branch"}',
        1
    )
    RETURNING id INTO v_branch_id;

    INSERT INTO mtr_spec_chem_limit (spec_id, branch_id, element, max_value, source)
    VALUES
        (v_spec_id, v_branch_id, 'c', 0.20, 'table'),
        (v_spec_id, v_branch_id, 'mn', 1.50, 'table'),
        (v_spec_id, v_branch_id, 'si', 0.50, 'table'),
        (v_spec_id, v_branch_id, 'p', 0.020, 'table'),
        (v_spec_id, v_branch_id, 's', 0.015, 'table'),
        (v_spec_id, v_branch_id, 'cu', 0.15, 'table'),
        (v_spec_id, v_branch_id, 'ni', 0.15, 'table'),
        (v_spec_id, v_branch_id, 'cr', 0.15, 'table'),
        (v_spec_id, v_branch_id, 'mo', 0.05, 'table'),
        (v_spec_id, v_branch_id, 'b', 0.003, 'table'),
        (v_spec_id, v_branch_id, 'nb', 0.05, 'table'),
        (v_spec_id, v_branch_id, 'ti', 0.03, 'table'),
        (v_spec_id, v_branch_id, 'v', 0.08, 'table');

    INSERT INTO mtr_spec_mech_limit (spec_id, branch_id, property, min_value, unit, specimen_size)
    VALUES
        (v_spec_id, v_branch_id, 'yield', 62000, 'psi', 'X1/X2'),
        (v_spec_id, v_branch_id, 'tensile', 69000, 'psi', 'X1/X2'),
        (v_spec_id, v_branch_id, 'elongation', 22, '%', 'X1/X2'),
        (v_spec_id, v_branch_id, 'hardness', 140, 'HBW', '');

    INSERT INTO mtr_spec_impact_limit (spec_id, branch_id, temperature, coupon_size, min_average, min_individual, unit, min_readings, orientation)
    VALUES
        (v_spec_id, v_branch_id, -40, 'A', 20, 10, 'ft-lbf', 3, 'longitudinal');

    INSERT INTO mtr_spec_condition_rule (spec_id, branch_id, target_element, condition_element, condition_type, condition_threshold, target_adjustment, target_new_max, description)
    VALUES
        (v_spec_id, v_branch_id, 'c', 'mn', 'above', 1.0, 0.0, 0.20, 'If Mn is above 1.0, cap C at 0.20');

    INSERT INTO mtr_spec_ce_threshold (spec_id, branch_id, thickness_min, thickness_max, max_ce)
    VALUES
        (v_spec_id, v_branch_id, 0.0, 4.0, 0.45);

    INSERT INTO mtr_spec_custom_rule (spec_id, branch_id, rule_type, label, field_name, operator, value_text, value_number, value_unit, description, raw_json)
    VALUES (
        v_spec_id,
        v_branch_id,
        'quality',
        'Manufacturer must contain Demo Mill',
        'manufacturer',
        'contains',
        'Demo Mill',
        NULL,
        '',
        'Manufacturer should contain Demo Mill',
        '{"rule_type":"quality","label":"Manufacturer must contain Demo Mill","field_name":"manufacturer","operator":"contains","value_text":"Demo Mill"}'
    );

    INSERT INTO mtr_spec_custom_rule (spec_id, branch_id, rule_type, label, field_name, operator, value_text, value_number, value_unit, description, raw_json)
    VALUES
        (v_spec_id, v_branch_id, 'identity', 'Grade must equal COVGRADE', 'grade', '=', 'COVGRADE', NULL, '', 'Exact grade check', '{"field_name":"grade","operator":"=","value_text":"COVGRADE"}'),
        (v_spec_id, v_branch_id, 'presence', 'Country of Melt must exist', 'country_of_melt', 'exists', NULL, NULL, '', 'Presence check', '{"field_name":"country_of_melt","operator":"exists"}'),
        (v_spec_id, v_branch_id, 'quality', 'Country of Manufacture must not be Canada', 'country_of_manufacture', '!=', 'Canada', NULL, '', 'Inequality check', '{"field_name":"country_of_manufacture","operator":"!=","value_text":"Canada"}'),
        (v_spec_id, v_branch_id, 'quality', 'Item number should start with COV', 'item_no', 'starts_with', 'COV', NULL, '', 'Prefix check', '{"field_name":"item_no","operator":"starts_with","value_text":"COV"}'),
        (v_spec_id, v_branch_id, 'quality', 'Description should end with inventory', 'description', 'ends_with', 'inventory', NULL, '', 'Suffix check', '{"field_name":"description","operator":"ends_with","value_text":"inventory"}'),
        (v_spec_id, v_branch_id, 'quality', 'Document number should be in list', 'document_no', 'in', 'COV-DOC-1,COV-DOC-2', NULL, '', 'List membership check', '{"field_name":"document_no","operator":"in","value_text":"COV-DOC-1,COV-DOC-2"}'),
        (v_spec_id, v_branch_id, 'quality', 'Lot number should not be in blocked list', 'lot_number', 'not_in', 'BAD-1,BAD-2', NULL, '', 'Negative list check', '{"field_name":"lot_number","operator":"not_in","value_text":"BAD-1,BAD-2"}'),
        (v_spec_id, v_branch_id, 'quality', 'Piece count must be greater than 1', 'piece_no', '>', NULL, 1, '', 'Numeric operator check', '{"field_name":"piece_no","operator":">","value_number":1}'),
        (v_spec_id, v_branch_id, 'quality', 'Weight must be at least 1000', 'weight', '>=', NULL, 1000, '', 'Numeric operator check', '{"field_name":"weight","operator":">=","value_number":1000}'),
        (v_spec_id, v_branch_id, 'quality', 'Direction should contain Long', 'direction', 'contains', 'Long', NULL, '', 'Substring check', '{"field_name":"direction","operator":"contains","value_text":"Long"}');

    INSERT INTO inventory (lot_number, heat_number, slab_number, item_no, dimensions, quantity, description, document_no, grade, image_path, weight, source_file)
    VALUES
        ('COV-LOT-PASS-LOT', 'COV-HEAT-OTHER', 'COV-BATCH-PASS', 'COV-ITEM-1', '1.50 x 48 x 120', 100, 'Coverage lot-match inventory', 'COV-DOC-1', 'COVGRADE', 'COV-IMAGE-1', 1200, 'demo_match_coverage_lab.csv'),
        ('COV-LOT-PASS-HEAT', 'COV-HEAT-PASS', 'COV-BATCH-OTHER-2', 'COV-ITEM-2', '1.50 x 48 x 120', 100, 'Coverage heat-match inventory', 'COV-DOC-2', 'COVGRADE', 'COV-IMAGE-2', 1200, 'demo_match_coverage_lab.csv'),
        ('COV-LOT-PASS-SLAB', 'COV-HEAT-OTHER-3', 'COV-BATCH-PASS', 'COV-ITEM-3', '1.50 x 48 x 120', 100, 'Coverage slab-match inventory', 'COV-DOC-3', 'COVGRADE', 'COV-IMAGE-3', 1200, 'demo_match_coverage_lab.csv'),
        ('COV-LOT-PASS-CERT', 'COV-HEAT-OTHER-4', 'COV-BATCH-OTHER-4', 'COV-ITEM-4', '1.50 x 48 x 120', 100, 'Coverage cert-match inventory', 'COV-DOC-4', 'COVGRADE', 'COV-CERT-PASS', 1200, 'demo_match_coverage_lab.csv'),
        ('COV-LOT-FAIL-CHEM', 'COV-HEAT-FAIL-CHEM', 'COV-BATCH-FAIL-CHEM', 'COV-ITEM-5', '1.50 x 48 x 120', 100, 'Coverage fail chemistry inventory', 'COV-DOC-5', 'COVGRADE', 'COV-IMAGE-5', 1200, 'demo_match_coverage_lab.csv'),
        ('COV-LOT-FAIL-MECH', 'COV-HEAT-FAIL-MECH', 'COV-BATCH-FAIL-MECH', 'COV-ITEM-6', '1.50 x 48 x 120', 100, 'Coverage fail mechanical inventory', 'COV-DOC-6', 'COVGRADE', 'COV-IMAGE-6', 1200, 'demo_match_coverage_lab.csv'),
        ('COV-LOT-FAIL-IMPACT', 'COV-HEAT-FAIL-IMPACT', 'COV-BATCH-FAIL-IMPACT', 'COV-ITEM-7', '1.50 x 48 x 120', 100, 'Coverage fail impact inventory', 'COV-DOC-7', 'COVGRADE', 'COV-IMAGE-7', 1200, 'demo_match_coverage_lab.csv'),
        ('COV-LOT-FAIL-CE', 'COV-HEAT-FAIL-CE', 'COV-BATCH-FAIL-CE', 'COV-ITEM-8', '1.50 x 48 x 120', 100, 'Coverage fail CE inventory', 'COV-DOC-8', 'COVGRADE', 'COV-IMAGE-8', 1200, 'demo_match_coverage_lab.csv'),
        ('COV-LOT-FAIL-CUSTOM', 'COV-HEAT-FAIL-CUSTOM', 'COV-BATCH-FAIL-CUSTOM', 'COV-ITEM-9', '1.50 x 48 x 120', 100, 'Coverage fail custom inventory', 'COV-DOC-9', 'COVGRADE', 'COV-IMAGE-9', 1200, 'demo_match_coverage_lab.csv'),
        ('COV-LOT-PASS-MM', 'COV-HEAT-PASS-MM', 'COV-BATCH-PASS-MM', 'COV-ITEM-10', '38.1 mm x 48 x 120', 100, 'Coverage mm thickness inventory', 'COV-DOC-10', 'COVGRADE', 'COV-IMAGE-10', 1200, 'demo_match_coverage_lab.csv');

    INSERT INTO mtr_data (
        batch_number,
        heat_number,
        certificate_number,
        grade,
        manufacturer,
        c_element,
        mn_element,
        si_element,
        p_element,
        s_element,
        b_element,
        v_element,
        nb_element,
        ti_element,
        al_element,
        ca_element,
        zr_element,
        zn_element,
        sn_element,
        cu_element,
        ni_element,
        cr_element,
        mo_element,
        n_element,
        yield_strength,
        tensile_strength,
        elongation,
        hardness,
        impact_test_temp,
        impact_coupon_size,
        impact_specimen_1,
        impact_specimen_2,
        impact_specimen_3,
        impact_average,
        thickness,
        plate_dimension,
        direction,
        country_of_melt,
        country_of_manufacture
    )
    VALUES
    (
        'COV-BATCH-PASS',
        'COV-HEAT-PASS',
        'COV-CERT-PASS',
        'COVGRADE',
        'Demo Mill and Supply',
        0.18,
        1.20,
        0.30,
        0.015,
        0.010,
        0.0004,
        0.0600,
        0.0300,
        0.0200,
        0.0300,
        0.0020,
        0.0010,
        0.0010,
        0.0010,
        0.1000,
        0.1200,
        0.1400,
        0.0300,
        0.0040,
        70000,
        80000,
        24,
        180,
        -50,
        'A',
        24,
        25,
        23,
        24,
        1.50,
        '1.50 x 48 x 120',
        'Longitudinal',
        'USA',
        'USA'
    ),
    (
        'COV-BATCH-FAIL-CHEM',
        'COV-HEAT-FAIL-CHEM',
        'COV-CERT-FAIL-CHEM',
        'COVGRADE',
        'Demo Mill and Supply',
        0.22,
        1.20,
        0.30,
        0.015,
        0.010,
        0.0004,
        0.0600,
        0.0300,
        0.0200,
        0.0300,
        0.0020,
        0.0010,
        0.0010,
        0.0010,
        0.1000,
        0.1200,
        0.1400,
        0.0300,
        0.0040,
        70000,
        80000,
        24,
        180,
        -50,
        'A',
        24,
        25,
        23,
        24,
        1.50,
        '1.50 x 48 x 120',
        'Longitudinal',
        'USA',
        'USA'
    ),
    (
        'COV-BATCH-FAIL-MECH',
        'COV-HEAT-FAIL-MECH',
        'COV-CERT-FAIL-MECH',
        'COVGRADE',
        'Demo Mill and Supply',
        0.18,
        1.20,
        0.30,
        0.015,
        0.010,
        0.0004,
        0.0600,
        0.0300,
        0.0200,
        0.0300,
        0.0020,
        0.0010,
        0.0010,
        0.0010,
        0.1000,
        0.1200,
        0.1400,
        0.0300,
        0.0040,
        50000,
        60000,
        24,
        180,
        -50,
        'A',
        24,
        25,
        23,
        24,
        1.50,
        '1.50 x 48 x 120',
        'Longitudinal',
        'USA',
        'USA'
    ),
    (
        'COV-BATCH-FAIL-IMPACT',
        'COV-HEAT-FAIL-IMPACT',
        'COV-CERT-FAIL-IMPACT',
        'COVGRADE',
        'Demo Mill and Supply',
        0.18,
        1.20,
        0.30,
        0.015,
        0.010,
        0.0004,
        0.0600,
        0.0300,
        0.0200,
        0.0300,
        0.0020,
        0.0010,
        0.0010,
        0.0010,
        0.1000,
        0.1200,
        0.1400,
        0.0300,
        0.0040,
        70000,
        80000,
        24,
        180,
        90,
        'A',
        24,
        25,
        23,
        24,
        1.50,
        '1.50 x 48 x 120',
        'Longitudinal',
        'USA',
        'USA'
    ),
    (
        'COV-BATCH-FAIL-CE',
        'COV-HEAT-FAIL-CE',
        'COV-CERT-FAIL-CE',
        'COVGRADE',
        'Demo Mill and Supply',
        0.20,
        1.30,
        0.30,
        0.015,
        0.010,
        0.0004,
        0.0600,
        0.0300,
        0.0200,
        0.0300,
        0.0020,
        0.0010,
        0.0010,
        0.0010,
        0.1000,
        0.1500,
        0.1500,
        0.0500,
        0.0040,
        70000,
        80000,
        24,
        180,
        -50,
        'A',
        24,
        25,
        23,
        24,
        1.50,
        '1.50 x 48 x 120',
        'Longitudinal',
        'USA',
        'USA'
    ),
    (
        'COV-BATCH-FAIL-CUSTOM',
        'COV-HEAT-FAIL-CUSTOM',
        'COV-CERT-FAIL-CUSTOM',
        'COVGRADE',
        'Other Mill',
        0.18,
        1.20,
        0.30,
        0.015,
        0.010,
        0.0004,
        0.0600,
        0.0300,
        0.0200,
        0.0300,
        0.0020,
        0.0010,
        0.0010,
        0.0010,
        0.1000,
        0.1200,
        0.1400,
        0.0300,
        0.0040,
        70000,
        80000,
        24,
        180,
        -50,
        'A',
        24,
        25,
        23,
        24,
        1.50,
        '1.50 x 48 x 120',
        'Longitudinal',
        'USA',
        'USA'
    ),
    (
        'COV-BATCH-PASS-MM',
        'COV-HEAT-PASS-MM',
        'COV-CERT-PASS-MM',
        'COVGRADE',
        'Demo Mill and Supply',
        0.18,
        1.20,
        0.30,
        0.015,
        0.010,
        0.0004,
        0.0600,
        0.0300,
        0.0200,
        0.0300,
        0.0020,
        0.0010,
        0.0010,
        0.0010,
        0.1000,
        0.1200,
        0.1400,
        0.0300,
        0.0040,
        70000,
        80000,
        24,
        180,
        -50,
        'A',
        24,
        25,
        23,
        24,
        1.50,
        '1.50 x 48 x 120',
        'Longitudinal',
        'USA',
        'USA'
    );

    INSERT INTO inventory (
        date,
        location_code,
        item_no,
        quantity,
        unit_of_measure_code,
        document_no,
        wsi_variant_code,
        dimensions,
        lot_number,
        heat_number,
        slab_number,
        internal_bin,
        additional_notes,
        cost_amount_actual,
        description_2,
        origin_code,
        picked,
        cutting_plan_no,
        image_path,
        entry_type,
        document_type,
        drawing,
        yield_value,
        document_line_no,
        revision,
        laser_quality,
        unitcost_cwt,
        piece_no,
        variant_code,
        description,
        return_reason_code,
        serial_no,
        package_no,
        invoiced_quantity,
        inventory_by_location,
        inventory,
        expiration_date,
        remaining_quantity,
        shipped_qty_not_returned,
        reserved_quantity,
        qty_per_unit_of_measure,
        sales_amount_expected,
        sales_amount_actual,
        cost_amount_expected,
        cost_amount_non_invtbl,
        item_description,
        cost_amount_expected_acy,
        cost_amount_actual_acy,
        completely_invoiced,
        cost_amount_non_invtbl_acy,
        assemble_to_order,
        drop_shipment,
        open_flag,
        order_type,
        order_no,
        order_line_no,
        prod_order_comp_line_no,
        entry_no,
        project_no,
        project_task_no,
        source_type,
        source_no,
        source_description,
        source_order_no,
        grade,
        weight,
        posting_date,
        country_of_melt,
        country_of_manufacture,
        source_file
    )
    VALUES (
        '2024-04-01',
        'A-01',
        'COV-ITEM-KITCHEN',
        100,
        'EA',
        'COV-DOC-1',
        'COVVAR',
        '1.50 x 48 x 120',
        'COV-LOT-KITCHEN',
        'COV-HEAT-KITCHEN',
        'COV-BATCH-KITCHEN',
        'BIN-1',
        'Kitchen sink inventory for matching coverage',
        123.45,
        'Desc 2',
        'USA',
        'Y',
        'CP-1',
        'COV-CERT-KITCHEN',
        'Positive Adjmt.',
        'Item Journal',
        'DWG-1',
        0,
        10,
        'R1',
        'LQ',
        12.34,
        12,
        'VAR-1',
        'Kitchen sink inventory',
        'RR-1',
        'SN-1',
        'PK-1',
        0,
        0,
        0,
        '2026-12-31',
        100,
        0,
        0,
        1,
        0,
        0,
        0,
        0,
        'Full field inventory record',
        0,
        0,
        'No',
        0,
        'No',
        'No',
        'Yes',
        'Blanket',
        'ORD-1',
        1000,
        2000,
        3000,
        'PRJ-1',
        'TASK-1',
        'Purchase',
        'SRC-1',
        'Source description',
        'SO-1',
        'COVGRADE',
        1200,
        '2024-04-02',
        'USA',
        'USA',
        'demo_match_coverage_lab.csv'
    );

    INSERT INTO mtr_data (
        batch_number,
        heat_number,
        certificate_number,
        grade,
        manufacturer,
        piece_no,
        c_element,
        mn_element,
        si_element,
        p_element,
        s_element,
        b_element,
        v_element,
        nb_element,
        ti_element,
        al_element,
        ca_element,
        zr_element,
        zn_element,
        sn_element,
        cu_element,
        ni_element,
        cr_element,
        mo_element,
        n_element,
        yield_strength,
        tensile_strength,
        elongation,
        reduction_area,
        hardness,
        impact_charpy,
        thickness,
        plate_dimension,
        direction,
        impact_test_temp,
        impact_coupon_size,
        impact_specimen_1,
        impact_specimen_2,
        impact_specimen_3,
        impact_average,
        country_of_melt,
        country_of_manufacture
    )
    VALUES (
        'COV-BATCH-KITCHEN',
        'COV-HEAT-KITCHEN',
        'COV-CERT-KITCHEN',
        'COVGRADE',
        'Demo Mill and Supply',
        12,
        0.18,
        1.20,
        0.30,
        0.015,
        0.010,
        0.0004,
        0.0600,
        0.0300,
        0.0200,
        0.0300,
        0.0020,
        0.0010,
        0.0010,
        0.0010,
        0.1000,
        0.1200,
        0.1400,
        0.0300,
        0.0040,
        70000,
        80000,
        24,
        55,
        180,
        18,
        1.50,
        '1.50 x 48 x 120',
        'Longitudinal',
        -50,
        'A',
        24,
        25,
        23,
        24,
        'USA',
        'USA'
    );

    RAISE NOTICE 'seeded MATCH COVERAGE LAB demo spec_id=%, branch_id=%', v_spec_id, v_branch_id;
END $$;
