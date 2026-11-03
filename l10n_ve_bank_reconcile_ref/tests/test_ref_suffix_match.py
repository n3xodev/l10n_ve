# Copyright 2026 andyengit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import RefReconcileCommon


@tagged("post_install", "-at_install")
class TestRefSuffixMatch(RefReconcileCommon):
    def assertReconciledWith(self, st_line, amls):
        self.assertTrue(st_line.is_reconciled)
        self.assertTrue(amls)
        self.assertTrue(all(aml.reconciled for aml in amls))

    def test_exact_payment_match_auto(self):
        payment = self._create_payment(1000.0, "78131243")
        st_line = self._create_st_line(1000.0, "REF 78-131243")
        self.assertReconciledWith(st_line, self._payment_aml(payment))

    def test_exact_ignores_leading_zeros(self):
        payment = self._create_payment(1000.0, "78131243")
        st_line = self._create_st_line(1000.0, "0078131243")
        self.assertReconciledWith(st_line, self._payment_aml(payment))

    def test_invoice_suffix_six_auto(self):
        invoice = self._create_invoice(500.0, "513367")
        st_line = self._create_st_line(500.0, "000084732513367")
        self.assertReconciledWith(st_line, self._invoice_aml(invoice))
        self.assertEqual(invoice.payment_state, "paid")

    def test_payment_suffix_four_auto(self):
        payment = self._create_payment(250.0, "9012")
        st_line = self._create_st_line(250.0, "00012349012")
        self.assertReconciledWith(st_line, self._payment_aml(payment))

    def test_statement_ref_field_is_searched(self):
        payment = self._create_payment(250.0, "345678")
        st_line = self._create_st_line(250.0, "Transfer", ref="00012345678")
        self.assertReconciledWith(st_line, self._payment_aml(payment))

    def test_payment_preferred_over_invoice(self):
        payment = self._create_payment(300.0, "345678")
        invoice = self._create_invoice(300.0, "345678")
        st_line = self._create_st_line(300.0, "00012345678")
        self.assertReconciledWith(st_line, self._payment_aml(payment))
        self.assertEqual(invoice.payment_state, "not_paid")

    def test_invoice_matched_when_no_payment(self):
        invoice = self._create_invoice(300.0, "345678")
        st_line = self._create_st_line(300.0, "00012345678")
        self.assertReconciledWith(st_line, self._invoice_aml(invoice))

    def test_invoice_first_when_payment_priority_disabled(self):
        self.bank_journal.l10n_ve_ref_match_payment_first = False
        self._create_payment(300.0, "345678")
        invoice = self._create_invoice(300.0, "345678")
        st_line = self._create_st_line(300.0, "00012345678")
        self.assertReconciledWith(st_line, self._invoice_aml(invoice))

    def test_custom_suffix_lengths(self):
        self.bank_journal.l10n_ve_ref_suffix_lengths = "8"
        self._create_payment(300.0, "345678")
        st_line = self._create_st_line(300.0, "00012345678")
        self.assertFalse(st_line.is_reconciled)

    def test_invalid_references_are_ignored(self):
        self._create_payment(100.0, "0")
        self._create_payment(100.0, "000000")
        for label in ("0", "00000000", "", "123", "N/A"):
            with self.subTest(label=label):
                st_line = self._create_st_line(100.0, label)
                self.assertFalse(st_line.is_reconciled)
                self.assertFalse(self._counterpart_amls(st_line))

    def test_amount_mismatch_is_not_reconciled(self):
        self._create_payment(1000.0, "345678")
        st_line = self._create_st_line(999.0, "00012345678")
        self.assertFalse(st_line.is_reconciled)
        self.assertFalse(self._counterpart_amls(st_line))

    def test_other_partner_payment_is_not_matched(self):
        self._create_payment(1000.0, "345678", partner=self.partner_b)
        st_line = self._create_st_line(1000.0, "00012345678")
        self.assertFalse(st_line.is_reconciled)

    def test_line_without_partner_matches_any_partner(self):
        payment = self._create_payment(1000.0, "345678")
        st_line = (
            self.env["account.bank.statement.line"]
            .with_context(_test_account_reconcile_oca=True)
            .create(
                {
                    "journal_id": self.bank_journal.id,
                    "amount": 1000.0,
                    "date": "2026-03-10",
                    "payment_ref": "00012345678",
                }
            )
        )
        self.assertReconciledWith(st_line, self._payment_aml(payment))

    def _create_ambiguous_case(self):
        first = self._create_payment(100.0, "7654321")
        second = self._create_payment(100.0, "1654321")
        st_line = self._create_st_line(100.0, "00099654321")
        return first, second, st_line

    def test_ambiguous_candidates_are_proposed_not_reconciled(self):
        first, second, st_line = self._create_ambiguous_case()
        self.assertFalse(st_line.is_reconciled)
        self.assertEqual(
            self._counterpart_amls(st_line),
            self._payment_aml(first) | self._payment_aml(second),
        )
        self.assertFalse(st_line.reconcile_data_info["can_reconcile"])
        self.assertFalse(st_line.can_reconcile)

    def test_ambiguous_direct_reconcile_is_refused(self):
        first, second, st_line = self._create_ambiguous_case()
        with self.assertRaises(UserError):
            st_line.reconcile_bank_line()
        self.assertFalse(st_line.is_reconciled)

    def test_ambiguous_without_partner(self):
        first = self._create_payment(100.0, "7654321")
        second = self._create_payment(100.0, "1654321")
        st_line = self._create_st_line(
            100.0, "00099654321", partner=self.env["res.partner"]
        )
        self.assertFalse(st_line.is_reconciled)
        self.assertEqual(
            self._counterpart_amls(st_line),
            self._payment_aml(first) | self._payment_aml(second),
        )

    def test_ambiguous_proposal_survives_a_reload(self):
        first, second, st_line = self._create_ambiguous_case()
        st_line.invalidate_recordset()
        self.assertEqual(
            self._counterpart_amls(st_line),
            self._payment_aml(first) | self._payment_aml(second),
        )
        self.assertFalse(st_line.can_reconcile)

    def test_ambiguous_user_removes_extra_candidate_and_reconciles(self):
        first, second, st_line = self._create_ambiguous_case()
        extra = self._payment_aml(second)
        # Same server path the widget uses to trash a line.
        st_line.manual_reference = f"account.move.line;{extra.id}"
        st_line.manual_delete = True
        st_line._onchange_manual_reconcile_reference()
        self.assertTrue(st_line.reconcile_data_info["can_reconcile"])
        self.assertEqual(self._counterpart_amls(st_line), self._payment_aml(first))
        st_line.reconcile_bank_line()
        self.assertTrue(st_line.is_reconciled)
        self.assertTrue(self._payment_aml(first).reconciled)
        self.assertFalse(extra.reconciled)

    def test_rerunning_auto_reconcile_does_not_duplicate_proposal(self):
        first, second, st_line = self._create_ambiguous_case()
        st_line._auto_reconcile()
        self.assertFalse(st_line.is_reconciled)
        self.assertEqual(
            self._counterpart_amls(st_line),
            self._payment_aml(first) | self._payment_aml(second),
        )
        self.assertEqual(
            len(
                [
                    line
                    for line in st_line.reconcile_data_info["data"]
                    if line["kind"] == "other"
                ]
            ),
            2,
        )

    def test_separators_in_stored_reference(self):
        payment = self._create_payment(1000.0, "78-131243")
        st_line = self._create_st_line(1000.0, "REF 78131243")
        self.assertReconciledWith(st_line, self._payment_aml(payment))

    def test_slashes_in_invoice_name(self):
        invoice = self._create_invoice(500.0, "UNRELATED")
        digits = re.sub(r"\D", "", invoice.name)
        st_line = self._create_st_line(500.0, f"FACT {digits}")
        self.assertReconciledWith(st_line, self._invoice_aml(invoice))

    def test_same_open_entry_is_not_claimed_twice_in_a_batch(self):
        payment = self._create_payment(100.0, "345678")
        lines = self._create_st_lines(
            [
                self._st_line_vals(100.0, "00012345678"),
                self._st_line_vals(100.0, "99912345678"),
            ]
        )
        self.assertEqual(len(lines.filtered("is_reconciled")), 1)
        self.assertTrue(self._payment_aml(payment).reconciled)

    def test_amount_mismatch_falls_through_to_next_step(self):
        self._create_payment(400.0, "345678")
        invoice = self._create_invoice(300.0, "345678")
        st_line = self._create_st_line(300.0, "00012345678")
        self.assertReconciledWith(st_line, self._invoice_aml(invoice))

    def test_search_limit_reached_is_never_auto_reconciled(self):
        self._create_payment(100.0, "345678")
        with patch(
            "odoo.addons.l10n_ve_bank_reconcile_ref.models."
            "account_bank_statement_line.AML_SEARCH_LIMIT",
            1,
        ):
            st_line = self._create_st_line(100.0, "00012345678")
        self.assertFalse(st_line.is_reconciled)
        self.assertFalse(self._counterpart_amls(st_line))

    def test_outbound_payment_matches_vendor_bill_line(self):
        payment = self._create_payment(
            200.0, "345678", partner=self.partner_b, payment_type="outbound"
        )
        st_line = self._create_st_line(-200.0, "00012345678", partner=self.partner_b)
        self.assertReconciledWith(st_line, self._payment_aml(payment))

    def test_vendor_bill_matched_on_outbound_line(self):
        bill = self._create_invoice(
            200.0, "345678", partner=self.partner_b, move_type="in_invoice"
        )
        st_line = self._create_st_line(-200.0, "00012345678", partner=self.partner_b)
        self.assertReconciledWith(st_line, self._invoice_aml(bill))

    def test_partially_paid_invoice_uses_residual(self):
        invoice = self._create_invoice(500.0, "345678")
        self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=invoice.ids
        ).create({"amount": 200.0})._create_payments()
        st_line = self._create_st_line(300.0, "00012345678")
        self.assertReconciledWith(st_line, self._invoice_aml(invoice))
        self.assertEqual(invoice.payment_state, "paid")

    def test_payment_from_another_journal_is_not_matched(self):
        other_journal = self.env["account.journal"].create(
            {"name": "Other bank", "type": "bank", "code": "OBNK"}
        )
        self._create_payment(100.0, "345678", journal=other_journal)
        st_line = self._create_st_line(100.0, "00012345678")
        self.assertFalse(st_line.is_reconciled)
        self.assertFalse(self._counterpart_amls(st_line))

    def test_payment_from_same_journal_is_matched(self):
        payment = self._create_payment(100.0, "345678", journal=self.bank_journal)
        st_line = self._create_st_line(100.0, "00012345678")
        self.assertReconciledWith(st_line, self._payment_aml(payment))
