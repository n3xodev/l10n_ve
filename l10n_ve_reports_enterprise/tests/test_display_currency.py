# Part of Odoo. See LICENSE file for full copyright and licensing details.

import io
import zipfile
import xml.etree.ElementTree as ET

from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account_reports.tests.common import TestAccountReportsCommon
from odoo.addons.account_reports.utils.report_data_objects import (
    AccountReportColumnData,
    AccountReportColumnFormatParamsData,
    AccountReportLineData,
)


@tagged("post_install", "-at_install")
class TestDisplayCurrencyEnterprise(TestAccountReportsCommon):
    """Test the Enterprise display currency selector options, conversion modes, and XLSX export."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_currency = cls.env.company.currency_id
        cls.foreign_currency = cls.env["res.currency"].create(
            {
                "name": "XVE",
                "symbol": "Xv",
                "rounding": 0.01,
                "active": True,
            }
        )
        # Rate on 2024-03-10: 1 company_currency = 2.0 XVE
        # Rate on 2024-03-20: 1 company_currency = 4.0 XVE
        # Rate today (or 2024-04-01+): 1 company_currency = 5.0 XVE
        cls.env["res.currency.rate"].create(
            [
                {
                    "currency_id": cls.foreign_currency.id,
                    "company_id": cls.env.company.id,
                    "name": "2024-03-10",
                    "rate": 2.0,
                },
                {
                    "currency_id": cls.foreign_currency.id,
                    "company_id": cls.env.company.id,
                    "name": "2024-03-20",
                    "rate": 4.0,
                },
                {
                    "currency_id": cls.foreign_currency.id,
                    "company_id": cls.env.company.id,
                    "name": "2024-04-01",
                    "rate": 5.0,
                },
            ]
        )

        cls.invoice = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.partner_a.id,
                "invoice_date": "2024-03-10",
                "date": "2024-03-10",
                "l10n_ve_control_number": "00-0000101",
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": cls.product_a.id,
                            "price_unit": 100.0,
                            "tax_ids": [Command.clear()],
                        }
                    )
                ],
            }
        )
        cls.invoice.action_post()

    def test_display_currency_options_initialization(self):
        report = self.env.ref("l10n_ve_reports_enterprise.diary_book_report")
        options = self._generate_options(report, "2024-03-01", "2024-03-31")
        self.assertEqual(options["display_currency_id"], self.company_currency.id)
        self.assertEqual(options["display_currency"]["id"], self.company_currency.id)
        self.assertTrue(options["available_currencies"])
        self.assertEqual(options["currency_rate_date_type"], "current")
        self.assertIsNone(options["currency_rate_date"])

        # Switch to foreign currency + manual date
        options_manual = self._generate_options(
            report,
            "2024-03-01",
            "2024-03-31",
            default_options={
                "display_currency_id": self.foreign_currency.id,
                "currency_rate_date_type": "manual",
                "currency_rate_date": "2024-03-20",
            },
        )
        self.assertEqual(options_manual["display_currency_id"], self.foreign_currency.id)
        self.assertEqual(options_manual["currency_rate_date_type"], "manual")
        self.assertEqual(options_manual["currency_rate_date"], "2024-03-20")
        self.assertEqual(
            options_manual["rounding_unit_names"]["units"],
            self.foreign_currency.symbol,
        )

    def test_conversion_modes_current_document_manual(self):
        report = self.env.ref("l10n_ve_reports_enterprise.diary_book_report")

        # 1. Manual mode on 2024-03-20 (rate = 4.0 -> 100 -> 400.0)
        opts_manual = self._generate_options(
            report,
            "2024-03-01",
            "2024-03-31",
            default_options={
                "display_currency_id": self.foreign_currency.id,
                "currency_rate_date_type": "manual",
                "currency_rate_date": "2024-03-20",
            },
        )
        val_manual = report.with_context(no_format=True)._format_value(
            opts_manual, 100.0, "monetary"
        )
        self.assertAlmostEqual(val_manual, 400.0, places=2)

        # 2. Current mode (today >= 2024-04-01 -> rate = 5.0 -> 100 -> 500.0)
        opts_current = self._generate_options(
            report,
            "2024-03-01",
            "2024-03-31",
            default_options={
                "display_currency_id": self.foreign_currency.id,
                "currency_rate_date_type": "current",
            },
        )
        expected_current = self.company_currency._convert(
            100.0, self.foreign_currency, self.env.company, fields.Date.today()
        )
        val_current = report.with_context(no_format=True)._format_value(
            opts_current, 100.0, "monetary"
        )
        self.assertAlmostEqual(val_current, expected_current, places=2)

        # 3. Document mode with line date 2024-03-10 (rate = 2.0 -> 100 -> 200.0)
        opts_doc = self._generate_options(
            report,
            "2024-03-01",
            "2024-03-31",
            default_options={
                "display_currency_id": self.foreign_currency.id,
                "currency_rate_date_type": "document",
            },
        )
        line = AccountReportLineData(
            id="test_doc_line",
            name="Test Document Line",
            columns=[
                AccountReportColumnData(
                    expression_label="date",
                    figure_type="date",
                    no_format=fields.Date.from_string("2024-03-10"),
                ),
                AccountReportColumnData(
                    expression_label="debit",
                    figure_type="monetary",
                    no_format=100.0,
                    format_params=AccountReportColumnFormatParamsData(
                        currency_id=self.company_currency.id
                    ),
                ),
            ],
        )
        report.with_context(no_format=True)._format_column_values(opts_doc, [line])
        self.assertAlmostEqual(line.columns[1].name, 200.0, places=2)
        self.assertEqual(line.columns[1].currency, self.foreign_currency)

    def test_no_double_conversion_for_preconverted_columns(self):
        report = self.env.ref("l10n_ve_reports_enterprise.diary_book_report")
        opts = self._generate_options(
            report,
            "2024-03-01",
            "2024-03-31",
            default_options={
                "display_currency_id": self.foreign_currency.id,
                "currency_rate_date_type": "manual",
                "currency_rate_date": "2024-03-20",
            },
        )
        # Value already in foreign_currency must NOT be converted again
        val = report.with_context(no_format=True)._format_value(
            opts,
            250.0,
            "monetary",
            format_params=AccountReportColumnFormatParamsData(
                currency_id=self.foreign_currency.id
            ),
        )
        self.assertAlmostEqual(val, 250.0, places=2)

    def test_xlsx_export_writes_converted_amounts(self):
        report = self.env.ref("l10n_ve_reports_enterprise.diary_book_report")
        opts = self._generate_options(
            report,
            "2024-03-01",
            "2024-03-31",
            default_options={
                "display_currency_id": self.foreign_currency.id,
                "currency_rate_date_type": "manual",
                "currency_rate_date": "2024-03-20",
            },
        )
        exported = report.export_to_xlsx(opts)
        self.assertEqual(exported["file_type"], "xlsx")
        self.assertTrue(exported["file_content"].startswith(b"PK"))

        # Verify that converted numeric value (400.0) appears in the first worksheet XML
        with zipfile.ZipFile(io.BytesIO(exported["file_content"])) as zf:
            sheet_xml = zf.read("xl/worksheets/sheet1.xml")
        root = ET.fromstring(sheet_xml)
        numeric_values = []
        for elem in root.iter():
            if elem.tag.endswith("}v") and elem.text:
                try:
                    numeric_values.append(float(elem.text))
                except ValueError:
                    pass
        self.assertTrue(
            any(abs(v - 400.0) < 0.01 for v in numeric_values),
            f"Expected converted amount 400.0 in XLSX cells, found: {numeric_values[:20]}",
        )
