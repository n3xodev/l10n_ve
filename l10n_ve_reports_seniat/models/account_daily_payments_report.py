# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class DailyPaymentsReportCustomHandler(models.AbstractModel):
    _inherit = "account.daily.payments.report.handler.oca"

    def _get_move_validation_date(self, move):
        return self._l10n_ve_seniat_get_move_validation_date(move)

    def _get_excluded_journal_ids(self, companies):
        return set(super()._get_excluded_journal_ids(companies)) | (
            self._l10n_ve_seniat_get_excluded_journal_ids(companies)
        )
