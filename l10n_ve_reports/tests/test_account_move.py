from unittest.mock import patch

from odoo import fields
from odoo.tests import tagged

from .common import TestAccountReportsCommon


@tagged("post_install", "-at_install")
class TestAccountMoveTaxClosing(TestAccountReportsCommon):
    def test_close_tax_period_resolves_handler(self):
        """_close_tax_period must resolve the tax report handler
        (models/account_move.py:185-186) instead of raising a registry
        KeyError, for the single-company case where the move's own company
        is its sender company.

        The PDF/export attachment step (``_get_vat_report_attachments``,
        which shells out to the PDF engine) is patched out: it is an
        unrelated infrastructure side effect of the full closing flow, not
        part of the model-name literal resolution under test here.
        """
        report = self.env.ref("account.generic_tax_report")
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.company_data["default_journal_misc"].id,
                "date": fields.Date.from_string("2024-01-31"),
                "tax_closing_report_id": report.id,
            }
        )
        self.assertEqual(move.state, "draft")

        options = move._get_tax_closing_report_options(
            move.company_id, move.fiscal_position_id, report, move.date
        )
        sender_company = report._get_sender_company_for_export(options)
        self.assertEqual(
            sender_company,
            move.company_id,
            "the single-company fixture must be its own sender company "
            "for the branch under test to execute",
        )

        # Must not raise KeyError('account.tax.report.handler').
        with patch.object(
            type(move), "_get_vat_report_attachments", return_value=[]
        ):
            move._close_tax_period(report, options)

    def test_refresh_tax_entry_uses_fallback_handler(self):
        """refresh_tax_entry must resolve the generic tax report handler
        fallback (models/account_move.py:360) when the report has no
        custom_handler_model_id configured, and dispatch
        _generate_tax_closing_entries on it.

        ``_generate_tax_closing_entries`` itself is mocked: its business
        logic (VAT closing computation, the bucket-12 tax group
        misconfiguration check ported in PR 2, and several Odoo
        19-incompatible fields still unported elsewhere in that flow) is
        unrelated pre-existing/out-of-scope work. This test only proves
        that the fallback handler model resolves (site 5) and is the one
        actually dispatched to.
        """
        report = self.env["account.report"].create(
            {
                "name": "Tax closing report without a custom handler",
            }
        )
        self.assertFalse(
            report.custom_handler_model_name,
            "the fixture report must leave custom_handler_model_name falsy "
            "to force the fallback branch under test",
        )

        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.company_data["default_journal_misc"].id,
                "date": fields.Date.from_string("2024-01-31"),
                "tax_closing_report_id": report.id,
            }
        )
        self.assertEqual(move.state, "draft")

        # Must not raise KeyError('account.generic.tax.report.handler').
        with patch.object(
            type(self.env["account.generic.tax.report.handler.oca"]),
            "_generate_tax_closing_entries",
        ) as mocked_generate:
            move.refresh_tax_entry()

        mocked_generate.assert_called_once()
        call_args = mocked_generate.call_args
        self.assertEqual(
            call_args.args[0],
            report,
            "the fallback handler must be dispatched with the move's own "
            "tax closing report",
        )
        self.assertEqual(
            call_args.kwargs.get("closing_moves"),
            move,
            "the fallback handler must be dispatched with the move being closed",
        )
