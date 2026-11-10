# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import Command
from odoo.tests import tagged

from odoo.addons.l10n_ve_seniat.tests.common import L10nVeSeniatCommon


@tagged("post_install", "-at_install")
class TestPosConsolidatedInvoice(L10nVeSeniatCommon):
    """Invoicing several POS orders together (``pos.make.invoice``) calls
    ``_create_invoice`` on a multi-record set."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.sudo().write(
            {"group_ids": [Command.link(cls.env.ref("point_of_sale.group_pos_manager").id)]}
        )
        cls.partner_ve = cls.env["res.partner"].create(
            {
                "name": "Consolidated POS customer",
                "country_id": cls.env.ref("base.ve").id,
                "vat": "J12345998",
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Consolidated POS product",
                "list_price": 100.0,
                "available_in_pos": True,
                "property_account_income_id": cls.company_data["default_account_revenue"].id,
            }
        )
        cls.ewallet_program = cls.env["loyalty.program"].create(
            {
                "name": "Consolidated ewallet",
                "program_type": "ewallet",
                "trigger": "auto",
                "applies_on": "future",
                "pos_ok": True,
                "reward_ids": [
                    Command.create(
                        {
                            "reward_type": "discount",
                            "discount_mode": "per_point",
                            "discount": 1,
                            "discount_applicability": "order",
                            "required_points": 1,
                            "description": "Ewallet",
                        }
                    )
                ],
            }
        )
        cls.reward = cls.ewallet_program.reward_ids[:1]
        cls.promo = cls.env["loyalty.program"].create(
            {
                "name": "Consolidated promo",
                "program_type": "promotion",
                "applies_on": "current",
                "trigger": "auto",
                "rule_ids": [Command.create({"minimum_qty": 1})],
                "reward_ids": [
                    Command.create(
                        {
                            "reward_type": "discount",
                            "discount": 10,
                            "discount_mode": "percent",
                            "discount_applicability": "order",
                            "required_points": 1,
                        }
                    )
                ],
            }
        )
        cls.promo_reward = cls.promo.reward_ids[:1]
        (cls.reward | cls.promo_reward).discount_line_product_id.property_account_income_id = (
            cls.company_data["default_account_revenue"]
        )
        cls.pay_later = cls.env["pos.payment.method"].create(
            {"name": "VE Consolidated Credit", "split_transactions": True}
        )
        cls.config = cls.env["pos.config"].create({"name": "Consolidated invoice POS"})
        cls.config.open_ui()
        cls.session = cls.config.current_session_id

    def _create_order(self, ewallet=0.0, promo=0.0):
        total = 100.0 - ewallet - promo
        lines = [
            Command.create(
                {
                    "product_id": self.product.id,
                    "qty": 1,
                    "price_unit": 100.0,
                    "price_subtotal": 100.0,
                    "price_subtotal_incl": 100.0,
                }
            )
        ]
        for amount, reward, code in (
            (ewallet, self.reward, "ewallet-reward"),
            (promo, self.promo_reward, "promo-reward"),
        ):
            if amount:
                lines.append(
                    Command.create(
                        {
                            "product_id": reward.discount_line_product_id.id,
                            "qty": 1,
                            "price_unit": -amount,
                            "price_subtotal": -amount,
                            "price_subtotal_incl": -amount,
                            "is_reward_line": True,
                            "reward_id": reward.id,
                            "reward_identifier_code": code,
                            "points_cost": amount,
                        }
                    )
                )
        order = self.env["pos.order"].create(
            {
                "company_id": self.env.company.id,
                "session_id": self.session.id,
                "partner_id": self.partner_ve.id,
                "state": "paid",
                "amount_tax": 0.0,
                "amount_total": total,
                "amount_paid": total,
                "amount_return": 0.0,
                "lines": lines,
            }
        )
        self.env["pos.payment"].create(
            {"pos_order_id": order.id, "payment_method_id": self.pay_later.id, "amount": total}
        )
        return order

    def _invoice_together(self, orders):
        wizard = (
            self.env["pos.make.invoice"]
            .with_context(active_ids=orders.ids, active_model="pos.order")
            .create({"consolidated_billing": True})
        )
        wizard.action_create_invoices()
        invoices = orders.account_move
        self.assertEqual(len(invoices), 1, "Orders must share one consolidated invoice")
        return invoices

    def test_consolidated_invoice_of_plain_orders(self):
        orders = self._create_order() | self._create_order()
        invoice = self._invoice_together(orders)
        self.assertEqual(invoice.country_code, "VE")

    def test_consolidated_invoice_transfers_each_order_discount_once(self):
        orders = self._create_order(promo=10.0) | self._create_order(promo=20.0)
        invoice = self._invoice_together(orders)
        self.assertEqual(len(invoice.l10n_ve_global_discount_ids), 2)
        self.assertAlmostEqual(
            sum(invoice.l10n_ve_global_discount_ids.mapped("amount")), 30.0, places=2
        )
        self.assertFalse(
            invoice.invoice_line_ids.filtered(
                lambda line: line.product_id == self.promo_reward.discount_line_product_id
            )
        )

    def test_consolidated_invoice_sums_ewallet_spend_in_one_note(self):
        orders = self._create_order(ewallet=30.0) | self._create_order(ewallet=20.0)
        invoice = self._invoice_together(orders)
        label = orders[:1]._l10n_ve_ewallet_payment_label()
        self.assertEqual((invoice.narration or "").count(label), 1)
        self.assertIn("50.00", invoice.narration)
        self.assertNotIn("30.00", invoice.narration)
        self.assertNotIn("20.00", invoice.narration)
        self.assertAlmostEqual(
            sum(invoice.l10n_ve_global_discount_ids.mapped("amount")), 50.0, places=2
        )
