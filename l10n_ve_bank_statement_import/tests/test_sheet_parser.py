from io import BytesIO

from openpyxl import Workbook

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

HEADER = ["Fecha", "Descripcion", "Monto"]
ROWS = [
    ["01/03/2026", "Deposito", "100.50"],
    ["02/03/2026", "Retiro", "-40.25"],
]


@tagged("post_install", "-at_install")
class TestSheetParserDispatch(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.parser = cls.env["account.statement.import.sheet.parser"]
        suspense = cls.env["account.account"].create(
            {"code": "987654", "name": "Suspense", "account_type": "asset_current"}
        )
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "Bank",
                "type": "bank",
                "code": "BNKT",
                "suspense_account_id": suspense.id,
            }
        )
        cls.mapping = cls.env["account.statement.import.sheet.mapping"].create(
            {
                "name": "Test mapping",
                "header_lines_skip_count": 1,
                "footer_lines_skip_count": 0,
                "float_thousands_sep": "comma",
                "float_decimal_sep": "dot",
                "delimiter": "comma",
                "quotechar": '"',
                "timestamp_format": "%d/%m/%Y",
                "timestamp_column": "Fecha",
                "amount_type": "simple_value",
                "amount_column": "Monto",
                "description_column": "Descripcion",
            }
        )

    def _parse(self, data, filename):
        parser = self.parser.with_context(journal_id=self.journal.id)
        return parser.parse(data, self.mapping, filename)

    def _assert_statement(self, result):
        _currency, _account, statements = result
        transactions = statements[0]["transactions"]
        self.assertEqual(
            [float(tx["amount"]) for tx in transactions], [100.50, -40.25]
        )

    @staticmethod
    def _csv():
        lines = [",".join(HEADER)] + [",".join(row) for row in ROWS]
        return "\n".join(lines).encode()

    @staticmethod
    def _html():
        def tr(cells, tag):
            return "<tr>%s</tr>" % "".join(f"<{tag}>{c}</{tag}>" for c in cells)

        body = tr(HEADER, "th") + "".join(tr(row, "td") for row in ROWS)
        return f"<table>{body}</table>".encode()

    @staticmethod
    def _xlsx():
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(HEADER)
        for row in ROWS:
            sheet.append(row)
        buffer = BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()

    def test_sheet_type_detection(self):
        self.assertEqual(self.parser._get_sheet_type(self._csv()), "csv")
        self.assertEqual(self.parser._get_sheet_type(self._html()), "html")
        self.assertEqual(self.parser._get_sheet_type(self._xlsx()), "xlsx")
        self.assertEqual(
            self.parser._get_sheet_type("BDVenlínea 01/03/2026".encode()),
            "bdv_comprobante",
        )

    def test_parse_csv(self):
        self._assert_statement(self._parse(self._csv(), "statement.csv"))

    def test_parse_html_table(self):
        self._assert_statement(self._parse(self._html(), "statement.html"))

    def test_parse_xlsx(self):
        self._assert_statement(self._parse(self._xlsx(), "statement.xlsx"))

    def test_parse_csv_skipping_lines_after_header(self):
        self.mapping.lines_skip_after_header = 1
        lines = [",".join(HEADER), "ignored,row,0"] + [",".join(r) for r in ROWS]
        data = "\n".join(lines).encode()
        self._assert_statement(self._parse(data, "statement.csv"))

    def test_parse_corrupt_xlsx_raises_user_error(self):
        corrupt = b"PK\x03\x04" + b"not a real workbook" * 8
        self.assertEqual(self.parser._get_sheet_type(corrupt), "xlsx")
        with self.assertRaisesRegex(UserError, "XLSX file could not be read"):
            self._parse(corrupt, "statement.xlsx")
