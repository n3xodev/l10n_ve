# Copyright 2026 andyengit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from .common import RefReconcileCommon


@tagged("post_install", "-at_install")
class TestRefMatchJournal(RefReconcileCommon):
    def test_defaults(self):
        journal = self.bank_journal
        self.assertTrue(journal.l10n_ve_ref_suffix_enabled)
        self.assertEqual(journal.l10n_ve_ref_suffix_lengths, "6,4")
        self.assertTrue(journal.l10n_ve_ref_match_payment_first)

    def test_suffix_lengths_parsing(self):
        journal = self.bank_journal
        cases = {
            "6,4": [6, 4],
            " 8 , 5 ,5": [8, 5],
            "3,2": [6, 4],
            "x,,": [6, 4],
            "": [6, 4],
            "10,4": [10, 4],
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                journal.l10n_ve_ref_suffix_lengths = value
                self.assertEqual(journal._l10n_ve_get_ref_suffix_lengths(), expected)

    def test_disabled_journal_leaves_line_untouched(self):
        self.bank_journal.l10n_ve_ref_suffix_enabled = False
        self._create_payment(1000.0, "345678")
        st_line = self._create_st_line(1000.0, "00012345678")
        self.assertFalse(st_line.is_reconciled)
        self.assertFalse(self._counterpart_amls(st_line))

    def test_oca_containment_match_still_works(self):
        invoice = self._create_invoice(750.0, "FACT-ABC")
        st_line = self._create_st_line(750.0, "FACT-ABC")
        self.assertTrue(st_line.is_reconciled)
        self.assertEqual(invoice.payment_state, "paid")

    def test_oca_containment_match_works_with_feature_disabled(self):
        self.bank_journal.l10n_ve_ref_suffix_enabled = False
        invoice = self._create_invoice(750.0, "FACT-ABC")
        st_line = self._create_st_line(750.0, "FACT-ABC")
        self.assertTrue(st_line.is_reconciled)
        self.assertEqual(invoice.payment_state, "paid")
