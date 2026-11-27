# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class DailyPaymentsReportCustomHandler(models.AbstractModel):
    _name = "account.daily.payments.report.handler.oca"
    _inherit = ["l10n.ve.daily.payments.mixin", "account.report.custom.handler.oca"]
    _description = "Daily Payments by Journal Report Custom Handler"

    def _get_custom_display_config(self):
        return {
            **super()._get_custom_display_config(),
            "templates": {
                "AccountReportFilters": (
                    "l10n_ve_reports.DailyPaymentsReportFiltersCustomizable"
                ),
            },
        }
