# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestSaleOrderCreateInvoiceNonVe(AccountTestInvoicingCommon):
    """Orders of a company outside Venezuela must fall through to the stock flow."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.sudo().write(
            {"group_ids": [Command.link(cls.env.ref("sales_team.group_sale_manager").id)]}
        )
        cls.partner = cls.env["res.partner"].create({"name": "Non VE customer"})
        cls.product = cls.env["product.product"].create(
            {"name": "Non VE product", "list_price": 100.0}
        )

    def _create_confirmed_order(self):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )
        order.action_confirm()
        return order

    def test_create_invoices_of_a_non_ve_company(self):
        order = self._create_confirmed_order()
        self.assertNotEqual(order.country_code, "VE")
        invoice = order._create_invoices()
        self.assertEqual(len(invoice), 1)
        self.assertEqual(invoice.move_type, "out_invoice")
        self.assertEqual(order.invoice_ids, invoice)
