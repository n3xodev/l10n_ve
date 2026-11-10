# Part of Odoo. See LICENSE file for full copyright and licensing details.

from unittest.mock import patch

from odoo import Command
from odoo.tests import tagged

from odoo.addons.l10n_ve_seniat.tests.common import L10nVeSeniatCommon

HOOK = "_l10n_ve_ewallet_partner"


@tagged("post_install", "-at_install")
class TestPosEwalletPartnerHook(L10nVeSeniatCommon):
    """The eWallet lookup goes through `_l10n_ve_ewallet_partner()`.

    The default is `partner_id`, so behavior is unchanged. Other modules override
    the hook to point the lookup at another partner.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.sudo().write(
            {"group_ids": [Command.link(cls.env.ref("point_of_sale.group_pos_manager").id)]}
        )
        Partner = cls.env["res.partner"]
        ve = cls.env.ref("base.ve")
        cls.partner = Partner.create({"name": "Ewallet customer", "country_id": ve.id})
        cls.other = Partner.create({"name": "Ewallet other holder", "country_id": ve.id})
        cls.product = cls.env["product.product"].create(
            {"name": "Ewallet hook product", "list_price": 10.0, "available_in_pos": True}
        )
        Program = cls.env["loyalty.program"]
        reward_vals = {
            "reward_type": "discount",
            "discount_mode": "per_point",
            "discount": 1,
            "discount_applicability": "order",
            "required_points": 1,
            "description": "Ewallet",
        }
        cls.program_a, cls.program_b = Program.create(
            [
                {
                    "name": f"Hook ewallet {suffix}",
                    "program_type": "ewallet",
                    "trigger": "auto",
                    "applies_on": "future",
                    "pos_ok": True,
                    "reward_ids": [(0, 0, dict(reward_vals))],
                }
                for suffix in ("A", "B")
            ]
        )
        # The order partner holds a card in program A, the other partner in program B.
        cls.card_partner = cls.env["loyalty.card"].create(
            {"program_id": cls.program_a.id, "partner_id": cls.partner.id, "points": 0}
        )
        cls.card_other = cls.env["loyalty.card"].create(
            {"program_id": cls.program_b.id, "partner_id": cls.other.id, "points": 0}
        )
        cls.config = cls.env["pos.config"].create({"name": "Ewallet hook POS"})
        cls.config.open_ui()
        cls.session = cls.config.current_session_id

    def _create_refund_order(self, amount=50.0):
        pay_later = self.env["pos.payment.method"].search([("journal_id", "=", False)], limit=1)
        if not pay_later:
            pay_later = self.env["pos.payment.method"].create(
                {"name": "VE Credit", "split_transactions": True}
            )
        order = self.env["pos.order"].create(
            {
                "company_id": self.env.company.id,
                "session_id": self.session.id,
                "partner_id": self.partner.id,
                "amount_tax": 0.0,
                "amount_total": -amount,
                "amount_paid": -amount,
                "amount_return": 0.0,
                "lines": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "qty": -1,
                            "price_unit": amount,
                            "price_subtotal": -amount,
                            "price_subtotal_incl": -amount,
                        },
                    )
                ],
            }
        )
        self.env["pos.payment"].create(
            {
                "pos_order_id": order.id,
                "payment_method_id": pay_later.id,
                "amount": -amount,
            }
        )
        return order

    def _hook_returning(self, partner):
        # Patch the registry class: it sits ahead of the base class in the MRO.
        return patch.object(
            type(self.env["pos.order"]), HOOK, lambda order: partner, create=True
        )

    def test_default_hook_returns_the_order_partner(self):
        order = self._create_refund_order()
        self.assertTrue(hasattr(order, HOOK), "pos.order must define the eWallet partner hook")
        self.assertEqual(getattr(order, HOOK)(), self.partner)
        order.partner_id = False
        self.assertFalse(getattr(order, HOOK)())

    def test_default_program_lookup_uses_the_order_partner_card(self):
        order = self._create_refund_order()
        self.assertEqual(order._l10n_ve_get_ewallet_program(), self.program_a)

    def test_program_lookup_goes_through_the_hook(self):
        order = self._create_refund_order()
        with self._hook_returning(self.other):
            self.assertEqual(order._l10n_ve_get_ewallet_program(), self.program_b)

    def test_default_refund_credit_goes_to_the_order_partner_card(self):
        order = self._create_refund_order(50.0)
        order._l10n_ve_credit_ewallet_from_pay_later_refund()
        self.assertTrue(order.l10n_ve_ewallet_credit_done)
        self.assertAlmostEqual(self.card_partner.points, 50.0, places=2)
        self.assertEqual(self.card_other.points, 0.0)

    def test_refund_credit_goes_through_the_hook(self):
        order = self._create_refund_order(50.0)
        with self._hook_returning(self.other):
            order._l10n_ve_credit_ewallet_from_pay_later_refund()
        self.assertTrue(order.l10n_ve_ewallet_credit_done)
        self.assertAlmostEqual(self.card_other.points, 50.0, places=2)
        self.assertEqual(self.card_partner.points, 0.0)

    def test_refund_credit_skipped_when_the_hook_returns_no_partner(self):
        order = self._create_refund_order(50.0)
        with self._hook_returning(self.env["res.partner"]):
            order._l10n_ve_credit_ewallet_from_pay_later_refund()
        self.assertFalse(order.l10n_ve_ewallet_credit_done)
        self.assertEqual(self.card_partner.points, 0.0)
        self.assertEqual(self.card_other.points, 0.0)
