# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import date

from odoo import Command, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from odoo.addons.l10n_ve_seniat.tests.common import L10nVeSeniatCommon


@tagged("post_install", "-at_install")
class TestFiscalReportsArcvAndIvaTxt(L10nVeSeniatCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company.partner_id.write({"vat": "J-12345678-9"})
        cls.supplier = cls.env["res.partner"].create(
            {
                "name": "Proveedor Reportes Fiscales",
                "country_id": cls.env.ref("base.ve").id,
                "vat": "V12345678",
                "supplier_rank": 1,
            }
        )
        cls.test_date = date(2026, 11, 15)
        cls.exempt_tax = cls.env["account.tax"].create(
            {
                "name": "Exento Compras Test",
                "amount": 0.0,
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "company_id": cls.company.id,
            }
        )
        cls.second_tax = cls.env["account.tax"].create(
            {
                "name": "IVA 8% Test",
                "amount": 8.0,
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "company_id": cls.company.id,
            }
        )

    def _create_vendor_bill(
        self,
        ref="FAC-001",
        control_number="00-000123",
        invoice_date=None,
        lines=None,
        currency=None,
    ):
        if lines is None:
            lines = [
                {
                    "name": "Compra gravada",
                    "quantity": 1.0,
                    "price_unit": 1000.0,
                    "account_id": self.company_data["default_account_expense"].id,
                    "tax_ids": [
                        Command.set([self.company_data["default_tax_purchase"].id])
                    ],
                }
            ]
        vals = {
            "move_type": "in_invoice",
            "partner_id": self.supplier.id,
            "invoice_date": invoice_date or self.test_date,
            "date": invoice_date or self.test_date,
            "ref": ref,
            "l10n_ve_control_number": control_number,
            "invoice_line_ids": [Command.create(line) for line in lines],
        }
        if currency:
            vals["currency_id"] = currency.id
        bill = self.env["account.move"].create(vals)
        bill.action_post()
        return bill

    def _create_iva_retention(
        self,
        move,
        *,
        ret_type="in_invoice",
        date_voucher=None,
        date_accounting=None,
        number="00202611000001",
        extra_lines=None,
    ):
        ret_lines = [
            Command.create(
                {
                    "name": "Línea IVA",
                    "move_id": move.id,
                    "invoice_amount": abs(move.amount_untaxed_signed),
                    "iva_amount": abs(move.amount_tax_signed),
                    "invoice_total": abs(move.amount_total_signed),
                    "aliquot": 16.0,
                    "retention_amount": abs(move.amount_tax_signed) * 0.75,
                }
            )
        ]
        if extra_lines:
            ret_lines.extend(Command.create(item) for item in extra_lines)
        return self.env["account.retention"].create(
            {
                "name": f"Ret IVA {number}",
                "type_retention": "iva",
                "type": ret_type,
                "partner_id": move.partner_id.id,
                "date": date_voucher or self.test_date,
                "date_accounting": date_accounting or self.test_date,
                "number": number,
                "state": "emitted",
                "retention_line_ids": ret_lines,
            }
        )

    # ------------------------------------------------------------------
    # ARCV tests
    # ------------------------------------------------------------------

    def test_arcv_empty_renders_without_error(self):
        wizard = self.env["arcv.report"].create(
            {
                "partner_id": self.supplier.id,
                "date_start": date(2026, 1, 1),
                "date_end": date(2026, 12, 31),
            }
        )
        action = wizard.print_arcv()
        self.assertEqual(
            action["report_name"], "l10n_ve_withholding.report_template_arcv"
        )
        data = action["data"]
        self.assertEqual(data["retentions"], [])
        self.assertEqual(data["partner"]["vat"], "V12345678")

        html, _ = self.env["ir.actions.report"]._render_qweb_html(
            "l10n_ve_withholding.action_report_arcv", None, data=data
        )
        self.assertIn(b"NO HAY DATOS", html)

    def test_arcv_rejects_inverted_dates(self):
        wizard = self.env["arcv.report"].create(
            {
                "partner_id": self.supplier.id,
                "date_start": date(2026, 12, 31),
                "date_end": date(2026, 1, 1),
            }
        )
        with self.assertRaises(ValidationError):
            wizard.print_arcv()

    def test_arcv_paid_amount_empty_returns_zero(self):
        empty_lines = self.env["account.retention.line"]
        result = empty_lines.get_invoice_paid_amount_not_related_with_retentions()
        self.assertEqual(result, 0.0)

    def test_arcv_partner_without_vat_formats_empty(self):
        partner_no_vat = self.env["res.partner"].create(
            {"name": "Sin RIF", "supplier_rank": 1}
        )
        wizard = self.env["arcv.report"].create(
            {
                "partner_id": partner_no_vat.id,
                "date_start": date(2026, 1, 1),
                "date_end": date(2026, 12, 31),
            }
        )
        action = wizard.print_arcv()
        self.assertEqual(action["data"]["partner"]["vat"], "")

    # ------------------------------------------------------------------
    # IVA TXT tests
    # ------------------------------------------------------------------

    def test_iva_txt_empty_ref_and_control_number_no_crash(self):
        bill = self._create_vendor_bill(ref=False, control_number="00-998877")
        retention = self._create_iva_retention(bill, number="0000123456")
        wizard = self.env["wizard.retention.iva"].create(
            {"date_start": date(2026, 11, 1), "date_end": date(2026, 11, 30)}
        )
        content = wizard._build_txt_content(retention)
        self.assertTrue(content.endswith("\r\n"))
        cols = content.rstrip("\r\n").split("\t")
        self.assertEqual(len(cols), 16)
        # Col 1: Company RIF normalized to 10 chars, no duplicate prefix
        self.assertEqual(cols[0], "J123456789")
        # Col 6: Supplier RIF zero-padded to 10 chars, no duplicate prefix
        self.assertEqual(cols[5], "V012345678")
        # Col 7: Falls back to move.name when ref is empty
        self.assertEqual(cols[6], bill.name)
        # Col 8: Reads l10n_ve_control_number, not ref
        self.assertEqual(cols[7], "00-998877")
        # Col 13: Preserves leading zeros
        self.assertEqual(cols[12], "0000123456")

    def test_iva_txt_filters_by_date_accounting_and_includes_refund_type(self):
        bill = self._create_vendor_bill(
            ref="FAC-NOV-01", invoice_date=date(2026, 11, 10)
        )
        # Voucher date in December, accounting date in November
        self._create_iva_retention(
            bill,
            ret_type="in_refund",
            date_voucher=date(2026, 12, 5),
            date_accounting=date(2026, 11, 20),
            number="2026110002",
        )
        wizard = self.env["wizard.retention.iva"].create(
            {"date_start": date(2026, 11, 1), "date_end": date(2026, 11, 30)}
        )
        action = wizard.generate_txt()
        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertNotIn("?&", action["url"])

        # Out-of-range period still raises UserError
        empty_wizard = self.env["wizard.retention.iva"].create(
            {"date_start": date(2026, 10, 1), "date_end": date(2026, 10, 31)}
        )
        with self.assertRaises(UserError):
            empty_wizard.generate_txt()

    def test_iva_txt_credit_note_col12_and_control_number_ui(self):
        bill = self._create_vendor_bill(ref="FAC-ORIG-01", control_number="00-111111")
        credit_note = self.env["account.move"].create(
            {
                "move_type": "in_refund",
                "partner_id": self.supplier.id,
                "invoice_date": self.test_date,
                "date": self.test_date,
                "ref": "NC-001",
                "l10n_ve_control_number": "00-222222",
                "reversed_entry_id": bill.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Devolución",
                            "quantity": 1.0,
                            "price_unit": 200.0,
                            "account_id": self.company_data[
                                "default_account_expense"
                            ].id,
                            "tax_ids": [
                                Command.set(
                                    [self.company_data["default_tax_purchase"].id]
                                )
                            ],
                        }
                    )
                ],
            }
        )
        # Verify control number UI is shown on draft vendor credit notes
        self.assertTrue(credit_note._l10n_ve_should_show_control_number_ui())
        credit_note.action_post()

        retention = self._create_iva_retention(
            credit_note, ret_type="in_refund", number="2026110003"
        )
        wizard = self.env["wizard.retention.iva"].create({})
        data = wizard._retention_iva(retention)
        self.assertEqual(data[0]["Tipo de documento"], "03")
        self.assertEqual(data[0]["Número de documento"], "NC-001")
        self.assertEqual(data[0]["Número de control"], "00-222222")
        self.assertEqual(data[0]["Número del documento afectado"], "FAC-ORIG-01")

    def test_iva_txt_exempt_multi_aliquot_no_crash_or_duplication(self):
        bill = self._create_vendor_bill(
            ref="FAC-MIX-01",
            control_number="00-555555",
            lines=[
                {
                    "name": "Línea 16%",
                    "quantity": 1.0,
                    "price_unit": 500.0,
                    "account_id": self.company_data["default_account_expense"].id,
                    "tax_ids": [
                        Command.set([self.company_data["default_tax_purchase"].id])
                    ],
                },
                {
                    "name": "Línea 8%",
                    "quantity": 1.0,
                    "price_unit": 200.0,
                    "account_id": self.company_data["default_account_expense"].id,
                    "tax_ids": [Command.set([self.second_tax.id])],
                },
                {
                    "name": "Línea exenta",
                    "quantity": 1.0,
                    "price_unit": 300.0,
                    "account_id": self.company_data["default_account_expense"].id,
                    "tax_ids": [Command.set([self.exempt_tax.id])],
                },
            ],
        )
        retention = self._create_iva_retention(
            bill,
            number="2026110004",
            extra_lines=[
                {
                    "name": "Línea IVA 8%",
                    "move_id": bill.id,
                    "invoice_amount": 200.0,
                    "iva_amount": 16.0,
                    "invoice_total": 216.0,
                    "aliquot": 8.0,
                    "retention_amount": 12.0,
                }
            ],
        )
        wizard = self.env["wizard.retention.iva"].create({})
        data = wizard._retention_iva(retention)
        self.assertEqual(len(data), 2)
        # Exempt amount emitted only once (not duplicated across aliquots)
        self.assertAlmostEqual(data[0]["Monto exento del IVA"], 300.0, places=2)
        self.assertAlmostEqual(data[1]["Monto exento del IVA"], 0.0, places=2)

    def test_iva_txt_exempt_amount_uses_company_currency(self):
        foreign_currency = (
            self.env.ref("base.EUR")
            if self.company.currency_id == self.env.ref("base.USD")
            else self.env.ref("base.USD")
        )
        foreign_currency.active = True
        self.env["res.currency.rate"].create(
            {
                "name": self.test_date,
                "currency_id": foreign_currency.id,
                "company_id": self.company.id,
                "rate": 0.02,  # 1 foreign = 50 company currency
            }
        )
        bill = self._create_vendor_bill(
            ref="FAC-FX-01",
            control_number="00-666666",
            currency=foreign_currency,
            lines=[
                {
                    "name": "Gravado FX",
                    "quantity": 1.0,
                    "price_unit": 100.0,
                    "account_id": self.company_data["default_account_expense"].id,
                    "tax_ids": [
                        Command.set([self.company_data["default_tax_purchase"].id])
                    ],
                },
                {
                    "name": "Exento FX",
                    "quantity": 1.0,
                    "price_unit": 20.0,
                    "account_id": self.company_data["default_account_expense"].id,
                    "tax_ids": [Command.set([self.exempt_tax.id])],
                },
            ],
        )
        retention = self._create_iva_retention(bill, number="2026110005")
        wizard = self.env["wizard.retention.iva"].create({})
        data = wizard._retention_iva(retention)
        # 20 foreign currency * 50 = 1000 company currency (not 20.0!)
        self.assertAlmostEqual(data[0]["Monto exento del IVA"], 1000.0, places=2)

    def test_iva_txt_sorted_by_date_accounting_asc(self):
        bill_late = self._create_vendor_bill(
            ref="FAC-LATE", invoice_date=date(2026, 11, 25)
        )
        bill_early = self._create_vendor_bill(
            ref="FAC-EARLY", invoice_date=date(2026, 11, 5)
        )
        ret_late = self._create_iva_retention(
            bill_late, date_accounting=date(2026, 11, 25), number="2026110010"
        )
        ret_early = self._create_iva_retention(
            bill_early, date_accounting=date(2026, 11, 5), number="2026110009"
        )
        wizard = self.env["wizard.retention.iva"].create({})
        data = wizard._retention_iva(ret_late | ret_early)
        self.assertEqual(
            [row["Número de documento"] for row in data],
            ["FAC-EARLY", "FAC-LATE"],
        )

    def test_iva_txt_format_rif_strips_iso_ve_prefix(self):
        partner = self.env["res.partner"].new({"vat": "VEJ123456789"})
        wizard = self.env["wizard.retention.iva"]
        self.assertEqual(wizard._format_seniat_rif(partner), "J123456789")

    def test_retention_voucher_report_values_uses_company_currency(self):
        bill = self._create_vendor_bill(ref="FAC-VOUCH-01")
        retention = self._create_iva_retention(bill, number="2026110020")
        report_model = self.env[
            "report.l10n_ve_withholding.retention_voucher_template"
        ]
        values = report_model._get_report_values(retention.ids)
        self.assertEqual(values["docs"], retention)
        self.assertEqual(
            values["get_digits"], self.company.currency_id.decimal_places
        )
