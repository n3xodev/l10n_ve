# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class L10nVeCashBookReportHandler(models.AbstractModel):
    _name = "l10n_ve.cash.book.report.handler"
    _inherit = [
        "l10n.ve.liquidity.book.mixin",
        "l10n.ve.enterprise.report.handler.mixin",
    ]
    _description = "Venezuela Enterprise Cash Book Report Handler"

    def _get_journal_types(self):
        return ["cash"]
