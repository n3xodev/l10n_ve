# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class L10nVeReportXHandler(models.AbstractModel):
    _name = "l10n_ve.report_x.handler"
    _inherit = [
        "l10n.ve.report.x.mixin",
        "l10n.ve.enterprise.report.handler.mixin",
    ]
    _description = "Venezuela Enterprise Report X Handler"

    def _get_daily_payments_handler(self):
        return self.env["l10n_ve.daily.payments.report.handler"]

    def _get_sales_book_handler(self):
        return self.env["l10n_ve.sales.book.report.handler"]
