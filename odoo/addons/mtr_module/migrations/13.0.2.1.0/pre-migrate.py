def migrate(cr, version):
    # All five limit tables moved their FK from spec_id to branch_id.
    # Any existing rows have branch_id = NULL and are invalid in the new schema.
    # Clear them so the upgrade can add the NOT NULL branch_id column safely.
    # Data is re-imported via n8n after upgrade.
    for table in (
        "mtr_spec_mech_limit",
        "mtr_spec_chem_limit",
        "mtr_spec_condition_rule",
        "mtr_spec_impact_limit",
        "mtr_spec_ce_threshold",
    ):
        cr.execute("SELECT to_regclass('public.%s')" % table)
        if cr.fetchone()[0]:
            cr.execute("DELETE FROM %s" % table)

