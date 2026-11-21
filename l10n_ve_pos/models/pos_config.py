from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    l10n_ve_invoice_journal_display_name = fields.Char(
        string="Invoice journal display name (VE POS)",
        related="journal_id.display_name",
        readonly=True,
    )
    l10n_ve_invoice_journal_emission_medium = fields.Selection(
        related="journal_id.l10n_ve_emission_medium",
        readonly=True,
    )
    l10n_ve_pos_free_book_section_name = fields.Char(
        compute="_compute_l10n_ve_pos_invoice_journal_ve_hints",
        string="VE talonario (forma libre)",
    )
    l10n_ve_pos_next_free_control_number = fields.Char(
        compute="_compute_l10n_ve_pos_invoice_journal_ve_hints",
        string="Próximo N° control (forma libre)",
    )

    @api.depends(
        "journal_id",
        "journal_id.l10n_ve_emission_medium",
        "journal_id.l10n_ve_invoice_section_id",
        "company_id.account_fiscal_country_id",
    )
    def _compute_l10n_ve_pos_invoice_journal_ve_hints(self):
        for config in self:
            config.l10n_ve_pos_free_book_section_name = False
            config.l10n_ve_pos_next_free_control_number = False
            if config.company_id.account_fiscal_country_id.code != "VE":
                continue
            journal = config.journal_id
            if not journal or journal.l10n_ve_emission_medium != "free":
                continue
            section = journal.l10n_ve_invoice_section_id
            if not section:
                continue
            book = section.book_id
            config.l10n_ve_pos_free_book_section_name = section.display_name
            if book:
                config.l10n_ve_pos_next_free_control_number = (
                    book.l10n_ve_peek_next_formatted(section) or ""
                )

    def l10n_ve_get_invoice_emission_preview(self, journal_id=False):
        """Fresh emission preview for the invoice journal (POS UI)."""
        self.ensure_one()
        self.invalidate_recordset(
            [
                "journal_id",
                "l10n_ve_invoice_journal_display_name",
                "l10n_ve_invoice_journal_emission_medium",
                "l10n_ve_pos_free_book_section_name",
                "l10n_ve_pos_next_free_control_number",
            ]
        )
        journal = (
            self.env["account.journal"].browse(journal_id)
            if journal_id
            else self.journal_id
        )
        if not journal:
            journal = self.journal_id
        medium = journal.l10n_ve_emission_medium if journal else False
        next_control = ""
        section_name = ""
        if (
            self.company_id.account_fiscal_country_id.code == "VE"
            and journal
            and medium == "free"
        ):
            section = journal.l10n_ve_invoice_section_id
            if section:
                section_name = section.display_name or ""
                book = section.book_id
                if book:
                    next_control = book.l10n_ve_peek_next_formatted(section) or ""
        return {
            "emission_medium": medium or "",
            "journal_display_name": journal.display_name if journal else "",
            "next_free_control_number": next_control,
            "free_book_section_name": section_name,
        }
