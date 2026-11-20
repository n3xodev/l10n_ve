# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError
from odoo.tests import new_test_user, tagged

from odoo.addons.l10n_ve_seniat.tests.common import L10nVeSeniatCommon


@tagged("post_install", "-at_install")
class TestL10nVeSaleLoyaltyIrAccess(L10nVeSeniatCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_basic = new_test_user(
            cls.env,
            login="ve_sl_basic",
            groups="base.group_user",
        )
        cls.user_salesman = new_test_user(
            cls.env,
            login="ve_sl_salesman",
            groups="base.group_user,sales_team.group_sale_salesman",
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Cliente Access VE",
                "country_id": cls.env.ref("base.ve").id,
                "vat": "J12345689",
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Producto Access VE",
                "company_id": cls.env.company.id,
                "list_price": 100.0,
                "taxes_id": [(6, 0, [cls.company_data["default_tax_sale"].id])],
            }
        )
        cls.reason = cls.env["l10n.ve.discount.reason"].sudo()._l10n_ve_get_default()
        if not cls.reason:
            cls.reason = cls.env["l10n.ve.discount.reason"].sudo().create(
                {"name": "Promoción"}
            )
        cls.order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "user_id": cls.user_salesman.id,
                "journal_id": cls.company_data["default_journal_sale"].id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "product_uom_qty": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )

    def test_discount_reason_access(self):
        reason_salesman = self.env["l10n.ve.discount.reason"].with_user(
            self.user_salesman
        )
        self.assertTrue(reason_salesman.browse(self.reason.id).name)
        with self.assertRaises(AccessError):
            reason_salesman.create({"name": "Forbidden"})
        with self.assertRaises(AccessError):
            reason_salesman.browse(self.reason.id).write({"name": "Forbidden"})
        with self.assertRaises(AccessError):
            reason_salesman.browse(self.reason.id).unlink()

        with self.assertRaises(AccessError):
            self.env["l10n.ve.discount.reason"].with_user(self.user_basic).search([])

    def test_sale_order_discount_access(self):
        discount_salesman = self.env["l10n.ve.sale.order.discount"].with_user(
            self.user_salesman
        )
        rec = discount_salesman.create(
            {
                "sale_order_id": self.order.id,
                "reason_id": self.reason.id,
                "discount_type": "fixed",
                "amount": 10.0,
            }
        )
        self.assertAlmostEqual(rec.amount, 10.0, places=2)
        rec.write({"amount": 15.0})
        self.assertAlmostEqual(rec.amount, 15.0, places=2)

        discount_basic = self.env["l10n.ve.sale.order.discount"].with_user(
            self.user_basic
        )
        with self.assertRaises(AccessError):
            discount_basic.browse(rec.id).read(["amount"])
        with self.assertRaises(AccessError):
            discount_basic.create(
                {
                    "sale_order_id": self.order.id,
                    "reason_id": self.reason.id,
                    "discount_type": "fixed",
                    "amount": 5.0,
                }
            )

        rec.unlink()
