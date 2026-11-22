from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.common import CommonPosTest


@tagged("post_install", "-at_install")
class TestL10nVePosData(CommonPosTest):
    """Server side of the Venezuelan POS: data loading, invoice journal, price lock."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.pos_config_usd
        cls.partner = cls.env["res.partner"].create({"name": "POS Partner"})
        cls.other_journal = cls.env["account.journal"].create(
            {
                "name": "Other POS sale journal",
                "type": "sale",
                "code": "OPSJ",
                "company_id": cls.company.id,
            }
        )

    def _invoiceable_order(self, refunds=None, **order_data):
        line = {"product_id": self.twenty_dollars_no_tax.product_variant_id.id}
        if refunds:
            line.update(refunded_orderline_id=refunds.lines[:1].id, qty=-1)
        order, _refund = self.create_backend_pos_order(
            {
                "pos_config": self.config,
                "order_data": {"partner_id": self.partner.id, **order_data},
                "line_data": [line],
            }
        )
        return order

    def _load_data(self):
        if not self.config.current_session_id:
            self.config.open_ui()
        return self.config.current_session_id.load_data()

    def test_session_loads_account_journal_after_pos_config(self):
        self.config.open_ui()
        models_list = self.config.current_session_id._load_pos_data_models(self.config)
        self.assertIn("account.journal", models_list)
        self.assertLess(models_list.index("pos.config"), models_list.index("account.journal"))

    def test_load_data_exposes_sale_journals_with_emission_medium(self):
        """``load_data`` fails on a ``_load_pos_data_domain`` with the Odoo 19 signature."""
        journal = self.config.journal_id
        journal.l10n_ve_emission_medium = "digital"
        data = self._load_data()
        journals = data["account.journal"]
        self.assertIn("l10n_ve_emission_medium", journals["fields"])
        loaded = {record["id"]: record for record in journals["records"]}
        self.assertEqual(loaded[journal.id]["l10n_ve_emission_medium"], "digital")
        self.assertIn(self.other_journal.id, loaded)
        self.assertTrue(
            all(
                record["type"] == "sale" and record["company_id"] == self.company.id
                for record in loaded.values()
            )
        )

    def test_load_data_exposes_the_pos_invoice_journal(self):
        data = self._load_data()
        self.assertEqual(
            data["pos.config"]["records"][0]["journal_id"],
            self.config.journal_id.id,
        )
        order_relations = data["pos.order"]["relations"]
        self.assertEqual(order_relations["invoice_journal_id"]["relation"], "account.journal")
        self.assertIn("l10n_ve_pos_fiscal_invoice_number", order_relations)

    def test_product_price_lock_flag_is_loaded(self):
        product = self.twenty_dollars_no_tax.product_variant_id
        product.l10n_ve_pos_allow_price_change = True
        self.assertTrue(product.product_tmpl_id.l10n_ve_pos_allow_price_change)
        data = self._load_data()
        self.assertIn("l10n_ve_pos_allow_price_change", data["product.product"]["fields"])
        record = next(r for r in data["product.product"]["records"] if r["id"] == product.id)
        self.assertTrue(record["l10n_ve_pos_allow_price_change"])

    def test_emission_preview_follows_the_selected_journal(self):
        self.other_journal.l10n_ve_emission_medium = "digital"
        self.config.journal_id.l10n_ve_emission_medium = "contingency"
        default = self.config.l10n_ve_get_invoice_emission_preview()
        self.assertEqual(default["emission_medium"], "contingency")
        self.assertEqual(default["journal_display_name"], self.config.journal_id.display_name)
        chosen = self.config.l10n_ve_get_invoice_emission_preview(self.other_journal.id)
        self.assertEqual(chosen["emission_medium"], "digital")
        self.assertEqual(chosen["journal_display_name"], self.other_journal.display_name)

    def test_config_hints_follow_the_pos_journal(self):
        self.config.journal_id.l10n_ve_emission_medium = "digital"
        self.assertEqual(self.config.l10n_ve_invoice_journal_emission_medium, "digital")
        self.assertEqual(
            self.config.l10n_ve_invoice_journal_display_name,
            self.config.journal_id.display_name,
        )

    def test_invoice_uses_the_order_journal(self):
        order = self._invoiceable_order(invoice_journal_id=self.other_journal.id)
        self.assertEqual(order._prepare_invoice_vals()["journal_id"], self.other_journal.id)

    def test_invoice_falls_back_to_the_pos_journal(self):
        order = self._invoiceable_order()
        self.assertFalse(order.invoice_journal_id)
        self.assertEqual(order._prepare_invoice_vals()["journal_id"], self.config.journal_id.id)

    def test_orders_with_different_journals_cannot_share_an_invoice(self):
        orders = self._invoiceable_order(
            invoice_journal_id=self.other_journal.id
        ) | self._invoiceable_order()
        with self.assertRaises(UserError):
            orders._l10n_ve_pos_effective_invoice_journal()

    def test_refund_is_locked_to_the_journal_of_the_original_order(self):
        origin = self._invoiceable_order(invoice_journal_id=self.other_journal.id)
        refund = self._invoiceable_order(refunds=origin)
        self.assertEqual(refund.refunded_order_id, origin)
        refund._l10n_ve_pos_lock_refund_invoice_journal()
        self.assertEqual(refund.invoice_journal_id, self.other_journal)

    def test_fiscal_fields_are_copied_to_the_invoice_once(self):
        order = self._invoiceable_order(
            l10n_ve_pos_fiscal_invoice_number="00000042",
            l10n_ve_pos_fiscal_serial="Z1A0000001",
            l10n_ve_pos_fiscal_report_z="0007",
        )
        move = self.env["account.move"].create(
            {"move_type": "out_invoice", "partner_id": self.partner.id}
        )
        order.account_move = move
        order._l10n_ve_pos_apply_fiscal_fields_to_move()
        self.assertEqual(move.l10n_ve_invoice_number, "00000042")
        self.assertEqual(move.l10n_ve_serial_number, "Z1A0000001")
        self.assertEqual(move.l10n_ve_report_z, "0007")
        self.assertTrue(move.l10n_ve_invoice_original_printed)
        # A number already set on the invoice is never overwritten.
        order.l10n_ve_pos_fiscal_invoice_number = "00000043"
        order._l10n_ve_pos_apply_fiscal_fields_to_move()
        self.assertEqual(move.l10n_ve_invoice_number, "00000042")
