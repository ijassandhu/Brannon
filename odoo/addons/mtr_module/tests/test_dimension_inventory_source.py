# -*- coding: utf-8 -*-
from odoo.tests.common import SavepointCase

from ..controllers.controllers import _build_filters_domain
from ..models.specs import _rule_subject_from_field


class TestDimensionInventorySource(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Mtr = cls.env["mtr.data"]
        cls.Inventory = cls.env["inventory.record"]

    def test_plate_dimension_reads_inventory_dimensions(self):
        mtr = self.Mtr.create({
            "batch_number": "B-1",
            "heat_number": "H-1",
            "certificate_number": "MT-1",
            "grade": "A36",
            "manufacturer": "Demo Mill",
        })
        inventory = self.Inventory.create({
            "lot_number": "LOT-1",
            "heat_number": "H-1",
            "slab_number": "B-1",
            "dimensions": "1.50 x 48 x 120",
        })
        mtr_values = {
            "c": None,
            "mn": None,
            "si": None,
            "p": None,
            "s": None,
            "cu": None,
            "ni": None,
            "cr": None,
            "mo": None,
            "n": None,
            "v": None,
        }

        subject = _rule_subject_from_field("plate_dimension", mtr, inventory, mtr_values)
        self.assertAlmostEqual(subject, 1.5, places=5)

        domain = _build_filters_domain([{
            "field": "plate_dimension",
            "op": "=",
            "value": "1.50 x 48 x 120",
        }])
        self.assertIn(("inv_dimensions", "ilike", "1.50 x 48 x 120"), domain)
        self.assertNotIn(("mtr_plate_dimension", "ilike", "1.50 x 48 x 120"), domain)
