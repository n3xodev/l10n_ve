from unittest.mock import patch

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from odoo.addons.l10n_ve_seniat.tests.common import L10nVeSeniatCommon


@tagged("post_install", "-at_install")
class TestL10nVeEdiCore(L10nVeSeniatCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.journal = cls.company_data["default_journal_sale"]
        cls.today = fields.Date.today()
        cls.account_only_user = cls.env["res.users"].create(
            {
                "name": "EDI Account Only",
                "login": "edi_account_only_user",
                "email": "edi_account_only@example.com",
                "company_id": cls.env.company.id,
                "company_ids": [Command.set([cls.env.company.id])],
                "group_ids": [
                    Command.set(
                        [
                            cls.env.ref("base.group_user").id,
                            cls.env.ref("account.group_account_invoice").id,
                        ]
                    )
                ],
            }
        )
        cls.account_stock_user = cls.env["res.users"].create(
            {
                "name": "EDI Account Stock",
                "login": "edi_account_stock_user",
                "email": "edi_account_stock@example.com",
                "company_id": cls.env.company.id,
                "company_ids": [Command.set([cls.env.company.id])],
                "group_ids": [
                    Command.set(
                        [
                            cls.env.ref("base.group_user").id,
                            cls.env.ref("account.group_account_invoice").id,
                            cls.env.ref("stock.group_stock_user").id,
                        ]
                    )
                ],
            }
        )

    def _create_out_invoice(self, post=False):
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "journal_id": self.journal.id,
                "invoice_date": self.today,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "EDI Test Line",
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "account_id": self.company_data["default_account_revenue"].id,
                            "tax_ids": [Command.set([self.company_data["default_tax_sale"].id])],
                        }
                    )
                ],
            }
        )
        if post:
            move.action_post()
        return move

    def test_mixin_parse_ve_vat_and_format_decimal(self):
        mixin = self.env["l10n_ve.edi.mixin"]
        self.assertEqual(mixin._l10n_ve_edi_parse_ve_vat("J-12345678-9"), ("J", "12345678-9"))
        self.assertEqual(mixin._l10n_ve_edi_parse_ve_vat("RIF v 12345678"), ("V", "12345678"))
        self.assertEqual(mixin._l10n_ve_edi_parse_ve_vat(""), ("", ""))
        self.assertEqual(mixin._l10n_ve_edi_format_decimal(-12.345), "12.35")
        self.assertEqual(mixin._l10n_ve_edi_format_decimal(0.0), "0.00")

    def test_unsent_dashboard_hidden_without_digital_provider(self):
        data = self.env["account.journal"].get_l10n_ve_edi_unsent_dashboard()
        self.assertFalse(data["visible"])
        self.assertEqual(data["items"], [])

    def test_unsent_dashboard_access_accounting_only_vs_stock_user(self):
        journal_cls = type(self.env["account.journal"])
        picking_cls = type(self.env["stock.picking"])
        with patch.object(
            journal_cls, "_l10n_ve_edi_digital_edi_available", return_value=True
        ):
            acct_journal = self.env["account.journal"].with_user(self.account_only_user)
            acct_data = acct_journal.get_l10n_ve_edi_unsent_dashboard()
            self.assertTrue(acct_data["visible"])
            acct_keys = [item["key"] for item in acct_data["items"]]
            self.assertIn("unsent_invoices", acct_keys)
            self.assertIn("unsent_retentions", acct_keys)

            inv_action = acct_journal.action_l10n_ve_edi_unsent_dashboard_open("unsent_invoices")
            self.assertEqual(inv_action["res_model"], "account.move")
            ret_action = acct_journal.action_l10n_ve_edi_unsent_dashboard_open("unsent_retentions")
            self.assertEqual(ret_action["res_model"], "account.retention")

            with patch.object(picking_cls, "has_access", return_value=False):
                no_stock_data = acct_journal.get_l10n_ve_edi_unsent_dashboard()
                no_stock_keys = [item["key"] for item in no_stock_data["items"]]
                self.assertNotIn("unsent_dispatch_guides", no_stock_keys)
                with patch.object(
                    picking_cls, "check_access", side_effect=AccessError("No stock read")
                ):
                    with self.assertRaises(AccessError):
                        acct_journal.action_l10n_ve_edi_unsent_dashboard_open(
                            "unsent_dispatch_guides"
                        )

            stock_journal = self.env["account.journal"].with_user(self.account_stock_user)
            stock_data = stock_journal.get_l10n_ve_edi_unsent_dashboard()
            stock_keys = [item["key"] for item in stock_data["items"]]
            self.assertIn("unsent_dispatch_guides", stock_keys)
            pick_action = stock_journal.action_l10n_ve_edi_unsent_dashboard_open(
                "unsent_dispatch_guides"
            )
            self.assertEqual(pick_action["res_model"], "stock.picking")

    def test_manual_send_and_retry_guards(self):
        draft = self._create_out_invoice(post=False)
        with self.assertRaises(UserError):
            draft.action_l10n_ve_edi_send()

        move = self._create_out_invoice(post=True)
        with self.assertRaises(UserError):
            move.action_l10n_ve_edi_send()

        move_cls = type(self.env["account.move"])
        with (
            patch.object(move_cls, "_l10n_ve_edi_is_invoice_target", return_value=True),
            patch.object(move_cls, "_build_payload_to_send", return_value={"ok": True}),
            patch.object(
                move_cls,
                "_l10n_ve_edi_schedule_send",
                new=lambda rec: rec._run_job(),
            ),
            patch.object(
                move_cls,
                "_l10n_ve_edi_dispatch_payload",
                return_value={"success": False, "error": "Temp error"},
            ),
        ):
            move.action_l10n_ve_edi_send()
            self.assertEqual(move.l10n_ve_edi_send_state, "failed")
            self.assertEqual(move.l10n_ve_edi_last_error, "Temp error")
            self.assertIn('"ok": true', move.l10n_ve_edi_payload_debug_json)

        with (
            patch.object(move_cls, "_l10n_ve_edi_is_invoice_target", return_value=True),
            patch.object(move_cls, "_build_payload_to_send", return_value={"ok": True}),
            patch.object(
                move_cls,
                "_l10n_ve_edi_schedule_send",
                new=lambda rec: rec._run_job(),
            ),
            patch.object(
                move_cls,
                "_l10n_ve_edi_dispatch_payload",
                return_value={"success": True, "response": {"codigo": 200}},
            ),
        ):
            move.action_l10n_ve_edi_retry_send()
            self.assertEqual(move.l10n_ve_edi_send_state, "sent")
            self.assertTrue(move.l10n_ve_edi_sent_at)

            with self.assertRaises(UserError):
                move.action_l10n_ve_edi_send()
