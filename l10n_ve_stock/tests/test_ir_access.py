# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged("post_install", "-at_install")
class TestL10nVeStockAccess(TransactionCase):
    """Operation-level checks for the ir.access rows converted for 20.0."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.basic = new_test_user(cls.env, "ve_stock_access_basic")
        cls.stock_user = new_test_user(
            cls.env, "ve_stock_access_user", groups="stock.group_stock_user"
        )
        cls.stock_manager = new_test_user(
            cls.env, "ve_stock_access_mgr", groups="stock.group_stock_manager"
        )

    def _access(self, user, model):
        records = self.env[model].with_user(user)
        return {
            op: records.has_access(op) for op in ("read", "create", "write", "unlink")
        }

    def test_transfer_reason_access(self):
        self.assertEqual(
            self._access(self.basic, "l10n_ve.stock.transfer.reason"),
            {"read": False, "create": False, "write": False, "unlink": False},
        )
        self.assertEqual(
            self._access(self.stock_user, "l10n_ve.stock.transfer.reason"),
            {"read": True, "create": False, "write": False, "unlink": False},
        )
        self.assertEqual(
            self._access(self.stock_manager, "l10n_ve.stock.transfer.reason"),
            {"read": True, "create": True, "write": True, "unlink": True},
        )
        reason = (
            self.env["l10n_ve.stock.transfer.reason"]
            .with_user(self.stock_manager)
            .create({"name": "Traslado prueba"})
        )
        self.assertEqual(
            reason.with_user(self.stock_user).name,
            "Traslado prueba",
        )
        with self.assertRaises(AccessError):
            reason.with_user(self.basic).read(["name"])
        with self.assertRaises(AccessError):
            reason.with_user(self.stock_user).write({"name": "No permitido"})

    def test_validate_confirmation_wizard_access(self):
        self.assertEqual(
            self._access(self.basic, "l10n_ve.stock.picking.validate.confirmation"),
            {"read": False, "create": False, "write": False, "unlink": False},
        )
        self.assertEqual(
            self._access(
                self.stock_user, "l10n_ve.stock.picking.validate.confirmation"
            ),
            {"read": True, "create": True, "write": True, "unlink": True},
        )
        picking_type = self.env["stock.picking.type"].search(
            [("code", "=", "outgoing"), ("company_id", "=", self.env.company.id)],
            limit=1,
        )
        picking = (
            self.env["stock.picking"]
            .with_user(self.stock_user)
            .create(
                {
                    "picking_type_id": picking_type.id,
                    "location_id": picking_type.default_location_src_id.id,
                    "location_dest_id": picking_type.default_location_dest_id.id,
                }
            )
        )
        wizard = (
            self.env["l10n_ve.stock.picking.validate.confirmation"]
            .with_user(self.stock_user)
            .create({"picking_ids": [(6, 0, picking.ids)]})
        )
        self.assertEqual(wizard.picking_ids, picking)
        with self.assertRaises(AccessError):
            self.env["l10n_ve.stock.picking.validate.confirmation"].with_user(
                self.basic
            ).create({"picking_ids": [(6, 0, picking.ids)]})
        wizard.unlink()

    def test_fleet_vehicle_read_access_for_stock_user(self):
        for model in ("fleet.vehicle", "fleet.vehicle.model", "fleet.vehicle.model.brand"):
            self.assertEqual(
                self._access(self.stock_user, model),
                {"read": True, "create": False, "write": False, "unlink": False},
            )
