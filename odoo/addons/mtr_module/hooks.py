# -*- coding: utf-8 -*-
import base64

from odoo import api, tools
from odoo import SUPERUSER_ID


def _drop_legacy_mtr_constraints(cr):
    """Remove old heat-only uniqueness so the composite key can work."""
    cr.execute("SELECT to_regclass('public.mtr_data')")
    if not cr.fetchone()[0]:
        return
    for index_name in (
        "mtr_data_mtr_heat_unique",
        "mtr_data_mtr_heat_batch_unique",
        "mtr_data_mtr_batch_unique",
        "mtr_data_mtr_certificate_heat_batch_unique",
    ):
        cr.execute(
            "SELECT 1 FROM pg_constraint WHERE conname = %s AND conrelid = 'mtr_data'::regclass",
            (index_name,),
        )
        if cr.fetchone():
            cr.execute("ALTER TABLE mtr_data DROP CONSTRAINT IF EXISTS %s" % index_name)
            continue
        cr.execute("DROP INDEX IF EXISTS %s" % index_name)


def pre_init_hook(cr):
    """Backfill blank certificate numbers so the new unique key can be applied safely."""
    _drop_legacy_mtr_constraints(cr)
    cr.execute("SELECT to_regclass('public.mtr_data')")
    if not cr.fetchone()[0]:
        return
    cr.execute(
        """
        UPDATE mtr_data
           SET certificate_number = COALESCE(NULLIF(certificate_number, ''), 'LEGACY-MTR-' || id::text)
         WHERE certificate_number IS NULL OR certificate_number = ''
        """
    )


def post_init_hook(cr, registry):
    """Ensure the module icon is stored in DB for Apps dashboard tiles."""
    _drop_legacy_mtr_constraints(cr)
    env = api.Environment(cr, SUPERUSER_ID, {})
    module = env["ir.module.module"].search([("name", "=", "mtr_module")], limit=1)
    if not module:
        return

    values = {"icon": "/mtr_module/static/description/icon.png"}
    if "icon_image" in module._fields:
        try:
            with tools.file_open("mtr_module/static/description/icon.png", "rb") as fh:
                values["icon_image"] = base64.b64encode(fh.read())
        except Exception:
            # Fallback to icon path if file read fails for any reason.
            pass

    module.write(values)
