# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.l10n_ve_seniat.tests.common import L10nVeSeniatCommon


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


@tagged("post_install", "-at_install")
class TestSaleOrderCreateInvoiceMixedBatch(L10nVeSeniatCommon):
    """One batch with orders of a VE company and of a non-VE company."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_ve = cls.env.company
        cls.company_other = cls.setup_other_company(name="Mixed batch other")["company"]
        cls.change_company_country(cls.company_other, cls.env.ref("base.us"))
        cls.env.user.sudo().write(
            {"company_ids": [Command.link(cls.company_other.id)]}
        )
        journal = cls.company_data["default_journal_sale"]
        cls._l10n_ve_configure_journal_digital(journal)

    def _create_confirmed_order(self, company, name):
        partner = self.env["res.partner"].create(
            {"name": name, "country_id": self.env.ref("base.ve").id, "vat": "J12345679"}
        )
        product = self.env["product.product"].create(
            {
                "name": f"Mixed batch {name}",
                "list_price": 100.0,
                "company_id": False,
                "categ_id": self.product_category.id,
            }
        )
        env = self.env(context=dict(self.env.context, allowed_company_ids=company.ids))
        order = env["sale.order"].create(
            {
                "company_id": company.id,
                "partner_id": partner.id,
                "order_line": [
                    Command.create(
                        {"product_id": product.id, "product_uom_qty": 1, "price_unit": 100.0}
                    )
                ],
            }
        )
        order.action_confirm()
        return order

    def test_batch_with_ve_and_non_ve_orders(self):
        ve_order = self._create_confirmed_order(self.company_ve, "Mixed VE")
        other_order = self._create_confirmed_order(self.company_other, "Mixed other")
        self.assertEqual(ve_order.country_code, "VE")
        self.assertNotEqual(other_order.country_code, "VE")
        moves = (ve_order | other_order)._create_invoices()
        self.assertEqual(ve_order.invoice_ids | other_order.invoice_ids, moves)
        self.assertEqual(len(moves), 2)
        self.assertEqual(len(ve_order.invoice_ids), 1)
        self.assertEqual(len(other_order.invoice_ids), 1)
