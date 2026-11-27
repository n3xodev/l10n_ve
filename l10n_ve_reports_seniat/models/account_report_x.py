# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class AccountVeReportXHandler(models.AbstractModel):
    _name = "account.ve.report_x.handler.oca"
    _inherit = ["l10n.ve.report.x.mixin", "account.report.custom.handler.oca"]
    _description = "Venezuela Reporte X (resumen consolidado)"

    def _get_daily_payments_handler(self):
        return self.env["account.daily.payments.report.handler.oca"]

    def _get_sales_book_handler(self):
        return self.env["account.sales.book.report.handler.oca"]
