# Copyright 2026 andyengit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

DEFAULT_SUFFIX_LENGTHS = "6,4"
MIN_SUFFIX_LENGTH = 4


class AccountJournal(models.Model):
    _inherit = "account.journal"

    l10n_ve_ref_suffix_enabled = fields.Boolean(
        string="Match by reference",
        default=True,
        help="Reconcile statement lines automatically with the open payment or "
        "invoice whose reference matches the bank reference, exactly or by its "
        "last digits.",
    )
    l10n_ve_ref_suffix_lengths = fields.Char(
        string="Suffix lengths",
        default=DEFAULT_SUFFIX_LENGTHS,
        help="Comma-separated suffix lengths to try in order, for example: 6,4. "
        "Values below 4 are ignored.",
    )
    l10n_ve_ref_match_payment_first = fields.Boolean(
        string="Match payments before invoices",
        default=True,
        help="Search open payments first, then open invoices and bills.",
    )

    def _l10n_ve_get_ref_suffix_lengths(self):
        """Return the valid suffix lengths configured on the journal, in order."""
        self.ensure_one()
        lengths = []
        for part in (self.l10n_ve_ref_suffix_lengths or "").split(","):
            part = part.strip()
            if not part.isdigit():
                continue
            length = int(part)
            if length >= MIN_SUFFIX_LENGTH and length not in lengths:
                lengths.append(length)
        return lengths or [int(n) for n in DEFAULT_SUFFIX_LENGTHS.split(",")]
