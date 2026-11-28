from odoo import api, models


class ArcvReport(models.AbstractModel):
    _name = "report.l10n_ve_withholding.report_template_arcv"
    _description = "AR-CV Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        return {
            "data": data,
            "currency": self.env.company.currency_id,
        }
