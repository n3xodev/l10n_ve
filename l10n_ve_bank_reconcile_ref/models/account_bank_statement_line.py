# Copyright 2026 andyengit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import models
from odoo.fields import Domain

INVOICE_MOVE_TYPES = (
    "out_invoice",
    "out_refund",
    "out_receipt",
    "in_invoice",
    "in_refund",
    "in_receipt",
)
AML_SEARCH_LIMIT = 200
MIN_TOKEN_LENGTH = 4


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def _do_auto_reconcile_invoices(self):
        """Complete the OCA containment match with the Venezuelan reference match.

        Lines left over by OCA are matched by exact reference or reference suffix.
        A single candidate with the exact amount is reconciled automatically.
        Several candidates are all proposed on the line, flagged as not
        reconcilable: each one covers the whole amount, so the user must remove the
        extra ones in the reconcile widget. That edit recomputes `can_reconcile`.
        """
        not_done, done = super()._do_auto_reconcile_invoices()
        proposed = self.browse()
        for line in not_done.filtered("journal_id.l10n_ve_ref_suffix_enabled"):
            amls = line._l10n_ve_find_reference_amls()
            if not amls:
                continue
            data_info = line._l10n_ve_build_reconcile_data(amls)
            if len(amls) > 1:
                data_info["can_reconcile"] = False
                line.reconcile_data_info = data_info
                proposed |= line
            elif data_info.get("can_reconcile"):
                line.reconcile_data_info = data_info
                done |= line
        return not_done - done - proposed, done

    # ------------------------------------------------------------------
    # Reconcile data
    # ------------------------------------------------------------------

    def _l10n_ve_build_reconcile_data(self, amls):
        """Build the reconcile widget data with `amls` as counterparts."""
        self.ensure_one()
        liquidity_lines, _suspense_lines, _other_lines = self._seek_for_lines()
        data = []
        reconcile_auxiliary_id = 1
        for line in liquidity_lines:
            reconcile_auxiliary_id, lines = self._get_reconcile_line(
                line,
                "liquidity",
                reconcile_auxiliary_id=reconcile_auxiliary_id,
                move=True,
            )
            data += lines
        for aml in amls:
            reconcile_auxiliary_id, lines = self._get_reconcile_line(
                aml,
                "other",
                is_counterpart=True,
                max_amount=self.amount_currency or self.amount,
                reconcile_auxiliary_id=reconcile_auxiliary_id,
                move=True,
            )
            data += lines
        return self._recompute_suspense_line(
            data, reconcile_auxiliary_id, self.manual_reference
        )

    # ------------------------------------------------------------------
    # Reference matching
    # ------------------------------------------------------------------

    def _l10n_ve_find_reference_amls(self):
        """Return the journal items matching the statement line reference and amount.

        The search goes by source (payments or invoices first) and by mode (exact
        digits, then each suffix length). The first step finding journal items by
        reference decides the result; among them only the ones with the exact amount
        are kept.
        """
        self.ensure_one()
        st_refs = self._l10n_ve_statement_ref_digits()
        if not st_refs:
            return self.env["account.move.line"]
        journal = self.journal_id
        sources = ("payment", "invoice")
        if not journal.l10n_ve_ref_match_payment_first:
            sources = sources[::-1]
        modes = [None, *journal._l10n_ve_get_ref_suffix_lengths()]
        for source in sources:
            for suffix_len in modes:
                amls = self._l10n_ve_search_reference_amls(source, st_refs, suffix_len)
                if amls:
                    return amls.filtered(self._l10n_ve_aml_amount_matches)
        return self.env["account.move.line"]

    def _l10n_ve_normalize_ref(self, value):
        """Keep the significant digits of a reference, or '' when it is unreliable."""
        digits = re.sub(r"\D", "", value or "")
        return digits.lstrip("0")

    def _l10n_ve_statement_ref_digits(self):
        """Return the normalized digit references found in the statement line."""
        self.ensure_one()
        refs = []
        for text in (self.payment_ref, self.ref):
            candidates = [text, *re.findall(rf"\d{{{MIN_TOKEN_LENGTH},}}", text or "")]
            for candidate in candidates:
                digits = self._l10n_ve_normalize_ref(candidate)
                if digits and digits not in refs:
                    refs.append(digits)
        return refs

    def _l10n_ve_aml_ref_digits(self, aml, source):
        """Return the normalized digit references stored on a journal item."""
        move = aml.move_id
        payment = aml.payment_id
        if source == "payment":
            values = [
                payment.payment_reference,
                payment.memo,
                payment.move_id.ref,
                payment.move_id.name,
                move.ref,
                move.name,
                aml.name,
                aml.ref,
            ]
        else:
            values = [move.payment_reference, move.ref, move.name, aml.name, aml.ref]
        refs = []
        for value in values:
            digits = self._l10n_ve_normalize_ref(value)
            if digits and digits not in refs:
                refs.append(digits)
        return refs

    def _l10n_ve_ref_matches(self, st_ref, aml_refs, suffix_len):
        """Check a statement reference against journal item references.

        With no `suffix_len` the digits must be equal. Otherwise both references must
        end with the same `suffix_len` digits.
        """
        if suffix_len is None:
            return st_ref in aml_refs
        if len(st_ref) < suffix_len:
            return False
        st_suffix = st_ref[-suffix_len:]
        return any(
            len(aml_ref) >= suffix_len and aml_ref[-suffix_len:] == st_suffix
            for aml_ref in aml_refs
        )

    def _l10n_ve_reference_amls_domain(self, source):
        """Open journal items of the given source the line could be reconciled with."""
        domain = Domain(self._get_default_amls_matching_domain())
        if self.partner_id:
            commercial_partner = self.partner_id.commercial_partner_id
            domain &= Domain("partner_id", "child_of", commercial_partner.id)
        if source == "payment":
            return domain & Domain("payment_id", "!=", False)
        return domain & Domain(
            [
                ("payment_id", "=", False),
                ("move_id.move_type", "in", INVOICE_MOVE_TYPES),
                (
                    "account_id.account_type",
                    "in",
                    ("asset_receivable", "liability_payable"),
                ),
            ]
        )

    def _l10n_ve_reference_text_domain(self, source, st_refs, suffix_len):
        """Pre-filter on the reference fields to keep the Python check small."""
        patterns = {
            st_ref if suffix_len is None else st_ref[-suffix_len:]
            for st_ref in st_refs
            if suffix_len is None or len(st_ref) >= suffix_len
        }
        if source == "payment":
            field_names = (
                "payment_id.payment_reference",
                "payment_id.memo",
                "move_id.ref",
                "move_id.name",
                "name",
                "ref",
            )
        else:
            field_names = (
                "move_id.payment_reference",
                "move_id.ref",
                "move_id.name",
                "name",
                "ref",
            )
        return Domain.OR(
            Domain(field_name, "ilike", pattern)
            for pattern in sorted(patterns)
            for field_name in field_names
        )

    def _l10n_ve_search_reference_amls(self, source, st_refs, suffix_len):
        """Search the journal items whose reference matches the statement references."""
        text_domain = self._l10n_ve_reference_text_domain(source, st_refs, suffix_len)
        if text_domain.is_false():
            return self.env["account.move.line"]
        domain = self._l10n_ve_reference_amls_domain(source) & text_domain
        amls = self.env["account.move.line"].search(domain, limit=AML_SEARCH_LIMIT)
        return amls.filtered(
            lambda aml: any(
                self._l10n_ve_ref_matches(
                    st_ref, self._l10n_ve_aml_ref_digits(aml, source), suffix_len
                )
                for st_ref in st_refs
            )
        )

    def _l10n_ve_aml_amount_matches(self, aml):
        """Check that the open amount of `aml` settles the statement line exactly."""
        self.ensure_one()
        transaction_amount, transaction_currency = (
            self._get_accounting_amounts_and_currencies()[:2]
        )
        counterpart = self._prepare_counterpart_amounts_using_st_line_rate(
            aml.currency_id, aml.amount_residual, aml.amount_residual_currency
        )
        residual = counterpart["amount_currency"] - transaction_amount
        return transaction_currency.is_zero(residual)
