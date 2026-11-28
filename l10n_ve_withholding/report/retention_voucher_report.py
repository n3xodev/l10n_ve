from odoo import _, api, models
from odoo.exceptions import ValidationError


class PaymentExtensionRetentionIvaVoucher(models.AbstractModel):
    _name = "report.l10n_ve_withholding.retention_voucher_template"
    _description = "Retention Voucher Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs_retentions = self.env["account.retention"].browse(docids)
        if any(
            retention.type_retention == "municipal" for retention in docs_retentions
        ):
            raise ValidationError(
                _("Municipal retentions do not have PDF voucher. Please print the xslx")
            )

        return {
            "docids": docids,
            "doc_model": "account.retention",
            "get_digits": self.get_digits(),
            "docs": docs_retentions,
        }

    def get_digits(self):
        return self.env.company.currency_id.decimal_places
