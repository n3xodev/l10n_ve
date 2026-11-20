from odoo.tests import tagged

from odoo.addons.stock.tests.common import TestStockCommon


@tagged("post_install", "-at_install")
class TestL10nVeStockReturnTransferReason(TestStockCommon):
    _test_user_groups = (
        "product.group_product_manager",
        "stock.group_stock_user",
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.write(
            {"account_fiscal_country_id": cls.env.ref("base.ve").id}
        )

    def test_return_incoming_picking_without_transfer_reason(self):
        picking_in = self.PickingObj.create(
            {
                "picking_type_id": self.picking_type_in.id,
                "location_id": self.supplier_location.id,
                "location_dest_id": self.stock_location.id,
            }
        )
        move = self.MoveObj.create(
            {
                "product_id": self.productA.id,
                "product_uom_qty": 5,
                "uom_id": self.uom_unit.id,
                "picking_id": picking_in.id,
                "location_id": self.supplier_location.id,
                "location_dest_id": self.stock_location.id,
            }
        )
        picking_in.action_confirm()
        picking_in.action_assign()
        move.quantity = 5
        picking_in.move_ids.picked = True
        picking_in.button_validate()

        action = picking_in.action_return()
        return_picking = self.env["stock.picking"].browse(action["res_id"])
        return_picking.action_return_all()

        self.assertTrue(return_picking.return_id)
        self.assertFalse(return_picking._l10n_ve_requires_internal_transfer_reason())

        return_picking.action_confirm()
        return_picking.action_assign()
        return_picking.move_ids.quantity = 5
        return_picking.move_ids.picked = True
        return_picking.button_validate()
