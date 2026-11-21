# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import Command
from odoo.tests import tagged

from odoo.addons.l10n_ve_reports.tests.common import TestAccountReportsCommon


@tagged("post_install", "-at_install")
class TestSeniatFiscalBookLines(TestAccountReportsCommon):
    """The fiscal books are built with the SQL helpers of the reports engine: make sure
    their lines are computed (queries, currency table, tax details) on Odoo 20."""

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

    def _lines(self, xml_id):
        report = self.env.ref(f"l10n_ve_reports_seniat.{xml_id}")
        options = self._generate_options(report, "2024-01-01", "2024-12-31")
        return report, options, report._get_lines(options)

    def _book_lines_of(self, report, lines, markup, move):
        """Lines of the book generated for ``move`` (parsed line id, not a substring match)."""
        return [
            line
            for line in lines
            if report._parse_line_id(line["id"], markup_as_string=True)[-1]
            == (markup, "account.move", move.id)
        ]

    def test_fiscal_books_compute_their_lines(self):
        for xml_id in (
            "sales_book_report",
            "purchases_book_report",
            "sales_book_fiscal_machine_report",
            "ve_report_x",
        ):
            with self.subTest(report=xml_id):
                report, options, lines = self._lines(xml_id)
                self.assertIsInstance(lines, list)
                for line in lines:
                    self.assertTrue(line["id"])
                    self.assertEqual(len(line["columns"]), len(options["columns"]))

    def test_sales_book_lists_the_posted_invoice(self):
        report, options, lines = self._lines("sales_book_report")
        listed = self._book_lines_of(report, lines, "sales_book_line", self.invoice)
        self.assertEqual(len(listed), 1, "the posted invoice must appear once")
        self.assertEqual(listed[0]["name"], self.invoice.name)
        values = {
            column["expression_label"]: listed[0]["columns"][index].get("no_format")
            for index, column in enumerate(options["columns"])
        }
        self.assertEqual(values["document_number"], self.invoice.name)
        self.assertEqual(values["correlative"], "00-0000001")
        self.assertEqual(values["move_type"], "FAC")
        self.assertEqual(values["partner_name"], self.partner_a.name)
        # 1000.0 + the sale tax of the test chart of accounts
        self.assertEqual(values["total_sales_iva"], self.invoice.amount_total)

    def test_purchases_book_lists_the_posted_bill(self):
        bill = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner_a.id,
                "invoice_date": "2024-03-16",
                "date": "2024-03-16",
                "ref": "BILL-2024-0001",
                "l10n_ve_control_number": "00-0000002",
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product_a.id,
                            "price_unit": 500.0,
                            "tax_ids": [Command.set(self.tax_purchase_a.ids)],
                        }
                    )
                ],
            }
        )
        bill.action_post()
        report, options, lines = self._lines("purchases_book_report")
        listed = self._book_lines_of(report, lines, "purchases_book_line", bill)
        self.assertEqual(len(listed), 1, "the posted bill must appear once")
        self.assertEqual(listed[0]["name"], "BILL-2024-0001")
        # the invoice is a sale: it is not in the purchases book
        self.assertFalse(
            self._book_lines_of(report, lines, "purchases_book_line", self.invoice)
        )
