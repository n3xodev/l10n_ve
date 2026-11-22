from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.common import CommonPosTest


@tagged("post_install", "-at_install")
class TestPosFiscalSerial(CommonPosTest):
    """Server side of the fiscal machine POS: data loading, preview, results."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids |= cls.env.ref("l10n_ve_seniat.group_seniat")
        cls.config = cls.pos_config_usd
        cls.machine = cls.env["l10n.ve.fiscal.machine"].create(
            {
                "name": "HKA POS test",
                "company_id": cls.company.id,
                "registered_serial": "Z1A0000099",
                "last_invoice_number": "00000041",
                "daily_closure_counter": "0006",
            }
        )
        cls.journal = cls.config.journal_id
        cls.journal.write(
            {
                "l10n_ve_emission_medium": "fiscal_machine",
                "l10n_ve_fiscal_machine_id": cls.machine.id,
            }
        )

    def _load_data(self):
        if not self.config.current_session_id:
            self.config.open_ui()
        return self.config.current_session_id.load_data()

    def _make_venezuelan(self):
        self.company.account_fiscal_country_id = self.env.ref("base.ve")

    def test_session_loads_fiscal_machines_before_journals(self):
        self.config.open_ui()
        models_list = self.config.current_session_id._load_pos_data_models(self.config)
        machine_model = "l10n.ve.fiscal.machine"
        self.assertIn(machine_model, models_list)
        self.assertLess(models_list.index("pos.config"), models_list.index(machine_model))
        self.assertLess(models_list.index(machine_model), models_list.index("account.journal"))

    def test_load_data_exposes_the_fiscal_machine_of_the_journal(self):
        """``load_data`` fails on a ``_load_pos_data_domain`` with the Odoo 19 signature."""
        data = self._load_data()
        machines = {r["id"]: r for r in data["l10n.ve.fiscal.machine"]["records"]}
        self.assertEqual(machines[self.machine.id]["registered_serial"], "Z1A0000099")
        self.assertEqual(machines[self.machine.id]["last_invoice_number"], "00000041")
        journals = {r["id"]: r for r in data["account.journal"]["records"]}
        self.assertEqual(journals[self.journal.id]["l10n_ve_fiscal_machine_id"], self.machine.id)

    def test_archived_and_foreign_machines_are_not_loaded(self):
        other_company = self.env["res.company"].create({"name": "Other fiscal company"})
        foreign = self.env["l10n.ve.fiscal.machine"].create(
            {"name": "Foreign", "company_id": other_company.id}
        )
        archived = self.machine.copy(
            {"name": "Archived", "active": False, "registered_serial": "Z1A0000098"}
        )
        loaded = {r["id"] for r in self._load_data()["l10n.ve.fiscal.machine"]["records"]}
        self.assertIn(self.machine.id, loaded)
        self.assertNotIn(foreign.id, loaded)
        self.assertNotIn(archived.id, loaded)

    def test_payment_method_fields_exist_on_odoo_20(self):
        """Reading a field Odoo 20 removed (``is_cash_count``) would break the POS start."""
        data = self._load_data()
        fields_list = data["pos.payment.method"]["fields"]
        self.assertIn("l10n_ve_fiscal_payment_code", fields_list)
        self.assertNotIn("is_cash_count", fields_list)
        self.assertNotIn("is_cash_count", self.env["pos.payment.method"]._fields)

    def test_company_flags_are_loaded(self):
        fields_list = self._load_data()["res.company"]["fields"]
        for name in ("l10n_ve_fiscal_flag_21", "l10n_ve_fiscal_flag_50", "l10n_ve_fiscal_use_barcode"):
            self.assertIn(name, fields_list)

    def test_fiscal_payment_code_follows_the_journal(self):
        journal = self.bank_payment_method.journal_id
        self.assertTrue(journal)
        journal.l10n_ve_fiscal_payment_code = "07"
        self.bank_payment_method.invalidate_recordset()
        self.assertEqual(self.bank_payment_method.l10n_ve_fiscal_payment_code, "07")

    def test_emission_preview_adds_the_next_fiscal_counters(self):
        self._make_venezuelan()
        preview = self.config.l10n_ve_get_invoice_emission_preview()
        self.assertEqual(preview["emission_medium"], "fiscal_machine")
        self.assertEqual(preview["next_fiscal_serial"], "Z1A0000099")
        self.assertEqual(preview["next_fiscal_invoice_number"], "00000042")
        self.assertEqual(preview["next_fiscal_report_z"], "0007")

    def test_emission_preview_is_empty_without_a_fiscal_machine_journal(self):
        self._make_venezuelan()
        other = self.env["account.journal"].create(
            {
                "name": "Digital POS journal",
                "type": "sale",
                "code": "DPJ",
                "company_id": self.company.id,
                "l10n_ve_emission_medium": "digital",
            }
        )
        preview = self.config.l10n_ve_get_invoice_emission_preview(other.id)
        self.assertEqual(preview["emission_medium"], "digital")
        self.assertEqual(preview["next_fiscal_invoice_number"], "")
        self.assertEqual(preview["next_fiscal_serial"], "")

    def test_report_z_button_only_while_closing_a_fiscal_machine_session(self):
        self._make_venezuelan()
        self.config.open_ui()
        session = self.config.current_session_id
        self.assertEqual(session.l10n_ve_journal_emission_medium, "fiscal_machine")
        self.assertFalse(session.l10n_ve_show_fiscal_report_z_button)
        session.state = "closing_control"
        self.assertTrue(session.l10n_ve_show_fiscal_report_z_button)
        self.journal.write({"l10n_ve_emission_medium": "digital"})
        session.invalidate_recordset()
        self.assertFalse(session.l10n_ve_show_fiscal_report_z_button)

    def test_print_result_without_invoice_is_stored_on_the_order(self):
        order, _refund = self.create_backend_pos_order(
            {
                "pos_config": self.config,
                "line_data": [{"product_id": self.twenty_dollars_no_tax.product_variant_id.id}],
            }
        )
        self.assertTrue(
            order.l10n_ve_fiscal_serial_register_print_result(
                {"data": {"sequence": 42, "serial_machine": "Z1A0000099", "mf_reportz": 7}}
            )
        )
        self.assertEqual(order.l10n_ve_pos_fiscal_invoice_number, "42")
        self.assertEqual(order.l10n_ve_pos_fiscal_serial, "Z1A0000099")
        self.assertEqual(order.l10n_ve_pos_fiscal_report_z, "7")

    def test_print_payload_requires_an_invoice(self):
        order, _refund = self.create_backend_pos_order(
            {
                "pos_config": self.config,
                "line_data": [{"product_id": self.twenty_dollars_no_tax.product_variant_id.id}],
            }
        )
        with self.assertRaises(UserError):
            order.l10n_ve_fiscal_serial_pos_fiscal_action_payload()
        with self.assertRaises(UserError):
            order.l10n_ve_fiscal_serial_register_print_result("not a dict")
