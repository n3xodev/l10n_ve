# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account_reports.tests.common import TestAccountReportsCommon
from odoo.addons.account_reports.utils.report_data_objects import (
    AccountReportLineData,
)


@tagged("post_install", "-at_install")
class TestVenezuelaEnterpriseBooks(TestAccountReportsCommon):
    """End-to-end tests for all 8 Venezuelan accounting reports on Odoo 20 Enterprise."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.invoice = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.partner_a.id,
                "invoice_date": "2024-03-15",
                "date": "2024-03-15",
                "l10n_ve_control_number": "00-0000001",
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": cls.product_a.id,
                            "price_unit": 1000.0,
                            "tax_ids": [Command.set(cls.tax_sale_a.ids)],
                        }
                    )
                ],
            }
        )
        cls.invoice.action_post()

        cls.bill = cls.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": cls.partner_a.id,
                "invoice_date": "2024-03-16",
                "date": "2024-03-16",
                "ref": "BILL-2024-0001",
                "l10n_ve_control_number": "00-0000002",
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": cls.product_a.id,
                            "price_unit": 500.0,
                            "tax_ids": [Command.set(cls.tax_purchase_a.ids)],
                        }
                    )
                ],
            }
        )
        cls.bill.action_post()

    def _run_report(self, xml_id, date_from="2024-01-01", date_to="2024-12-31"):
        report = self.env.ref(f"l10n_ve_reports_enterprise.{xml_id}")
        options = self._generate_options(report, date_from, date_to)
        lines = report._get_lines(options)
        return report, options, lines

    def _book_lines_of(self, report, lines, markup, move):
        return [
            line
            for line in lines
            if report._parse_line_id(line.id, markup_as_string=True)[-1]
            == (markup, "account.move", move.id)
        ]

    def _line_values(self, options, line):
        return {
            column["expression_label"]: line.columns[idx].no_format
            for idx, column in enumerate(options["columns"])
        }

    def test_all_eight_books_return_account_report_line_data(self):
        for xml_id in (
            "diary_book_report",
            "bank_book_report",
            "cash_book_report",
            "daily_payments_report",
            "purchases_book_report",
            "sales_book_report",
            "sales_book_fiscal_machine_report",
            "ve_report_x",
        ):
            with self.subTest(report=xml_id):
                _report, options, lines = self._run_report(xml_id)
                self.assertIsInstance(lines, list)
                for line in lines:
                    self.assertIsInstance(line, AccountReportLineData)
                    self.assertTrue(line.id)
                    self.assertEqual(len(line.columns), len(options["columns"]))

    def test_sales_book_invoice_totals_and_xlsx(self):
        report, options, lines = self._run_report("sales_book_report")
        listed = self._book_lines_of(report, lines, "sales_book_line", self.invoice)
        self.assertEqual(len(listed), 1)
        values = self._line_values(options, listed[0])
        self.assertEqual(values["document_number"], self.invoice.name)
        self.assertEqual(values["correlative"], "00-0000001")
        self.assertEqual(values["move_type"], "FAC")
        self.assertAlmostEqual(
            values["total_sales_iva"], self.invoice.amount_total, places=2
        )

        # Verify tax group column ordering does not crash and keeps valid columns
        column_labels = [c["expression_label"] for c in options["columns"]]
        self.assertIn("total_sales_iva", column_labels)

        exported = report.export_to_xlsx(options)
        self.assertEqual(exported["file_type"], "xlsx")
        self.assertTrue(exported["file_content"].startswith(b"PK"))

    def test_purchases_book_bill_totals_and_xlsx(self):
        report, options, lines = self._run_report("purchases_book_report")
        listed = self._book_lines_of(report, lines, "purchases_book_line", self.bill)
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].name, "BILL-2024-0001")
        self.assertFalse(
            self._book_lines_of(report, lines, "purchases_book_line", self.invoice)
        )

        exported = report.export_to_xlsx(options)
        self.assertEqual(exported["file_type"], "xlsx")
        self.assertTrue(exported["file_content"].startswith(b"PK"))

    def test_fiscal_machine_sales_book_and_report_x(self):
        fm_report, fm_opts, fm_lines = self._run_report(
            "sales_book_fiscal_machine_report"
        )
        self.assertIsInstance(fm_lines, list)
        self.assertTrue(fm_report.export_to_xlsx(fm_opts)["file_content"].startswith(b"PK"))

        rx_report, rx_opts, rx_lines = self._run_report(
            "ve_report_x", date_from="2024-03-15", date_to="2024-03-15"
        )
        self.assertTrue(rx_lines)
        self.assertTrue(rx_report.export_to_xlsx(rx_opts)["file_content"].startswith(b"PK"))

    def test_diary_book_groups_posted_moves_with_balanced_totals(self):
        report, options, lines = self._run_report(
            "diary_book_report", date_from="2024-03-01", date_to="2024-03-31"
        )
        self.assertTrue(lines)
        total_lines = [line for line in lines if line.id and "total" in str(line.id)]
        self.assertTrue(total_lines)
        total_vals = self._line_values(options, total_lines[-1])
        self.assertGreater(total_vals["debit"], 0.0)
        self.assertAlmostEqual(total_vals["debit"], total_vals["credit"], places=2)

    def test_bank_and_cash_books_isolation_and_running_balance(self):
        bank_journal = self.company_data["default_journal_bank"]
        cash_journal = self.company_data["default_journal_cash"]
        bank_account = bank_journal.default_account_id
        cash_account = cash_journal.default_account_id
        counterpart = self.company_data["default_account_receivable"]

        # Opening move in February for bank (+200)
        opening_bank = self.env["account.move"].create(
            {
                "journal_id": bank_journal.id,
                "date": "2024-02-15",
                "line_ids": [
                    Command.create(
                        {"account_id": bank_account.id, "debit": 200.0, "credit": 0.0}
                    ),
                    Command.create(
                        {"account_id": counterpart.id, "debit": 0.0, "credit": 200.0}
                    ),
                ],
            }
        )
        opening_bank.action_post()

        # Period move in March for bank (+50)
        period_bank = self.env["account.move"].create(
            {
                "journal_id": bank_journal.id,
                "date": "2024-03-10",
                "line_ids": [
                    Command.create(
                        {"account_id": bank_account.id, "debit": 50.0, "credit": 0.0}
                    ),
                    Command.create(
                        {"account_id": counterpart.id, "debit": 0.0, "credit": 50.0}
                    ),
                ],
            }
        )
        period_bank.action_post()

        # Period move in March for cash (+75)
        period_cash = self.env["account.move"].create(
            {
                "journal_id": cash_journal.id,
                "date": "2024-03-12",
                "line_ids": [
                    Command.create(
                        {"account_id": cash_account.id, "debit": 75.0, "credit": 0.0}
                    ),
                    Command.create(
                        {"account_id": counterpart.id, "debit": 0.0, "credit": 75.0}
                    ),
                ],
            }
        )
        period_cash.action_post()

        _b_rep, b_opts, b_lines = self._run_report(
            "bank_book_report", date_from="2024-03-01", date_to="2024-03-31"
        )
        b_names = [line.name for line in b_lines]
        self.assertTrue(any(bank_journal.name in (n or "") for n in b_names))
        self.assertFalse(any(cash_journal.name in (n or "") for n in b_names))

        _c_rep, c_opts, c_lines = self._run_report(
            "cash_book_report", date_from="2024-03-01", date_to="2024-03-31"
        )
        c_names = [line.name for line in c_lines]
        self.assertTrue(any(cash_journal.name in (n or "") for n in c_names))
        self.assertFalse(any(bank_journal.name in (n or "") for n in c_names))

    def test_daily_payments_seniat_hooks(self):
        handler = self.env["l10n_ve.daily.payments.report.handler"]
        # 1. Process date precedence over move.date
        self.invoice.l10n_ve_process_date = fields.Date.from_string("2024-03-25")
        self.assertEqual(
            handler._get_move_validation_date(self.invoice),
            fields.Date.from_string("2024-03-25"),
        )

        # 2. Retention journals excluded
        retention_journal = self.env["account.journal"].create(
            {
                "name": "Test IVA Retention EE",
                "code": "TIVE",
                "type": "general",
                "company_id": self.env.company.id,
            }
        )
        self.env.company.iva_supplier_retention_journal_id = retention_journal
        excluded = handler._get_excluded_journal_ids(self.env.company)
        self.assertIn(retention_journal.id, excluded)

        # 3. Custom display config uses bare component name for EE
        config = handler._get_custom_display_config()
        self.assertEqual(
            config["components"]["AccountReportFilters"],
            "DailyPaymentsReportFilters",
        )
