# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class L10nVeDailyPaymentsReportHandler(models.AbstractModel):
    _name = "l10n_ve.daily.payments.report.handler"
    _inherit = [
        "l10n.ve.daily.payments.mixin",
        "l10n.ve.enterprise.report.handler.mixin",
    ]
    _description = "Venezuela Enterprise Daily Payments Report Handler"

    def _get_move_validation_date(self, move):
        return self._l10n_ve_seniat_get_move_validation_date(move)

    def _get_excluded_journal_ids(self, companies):
        return set(super()._get_excluded_journal_ids(companies)) | (
            self._l10n_ve_seniat_get_excluded_journal_ids(companies)
        )

    def _get_custom_display_config(self):
        return {
            **super()._get_custom_display_config(),
            "components": {
                "AccountReportFilters": "DailyPaymentsReportFilters",
            },
        }
