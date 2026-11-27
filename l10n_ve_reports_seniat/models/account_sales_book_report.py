# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class SalesBookReportCustomHandler(models.AbstractModel):
    _name = "account.sales.book.report.handler.oca"
    _inherit = ["l10n.ve.sales.book.mixin", "account.report.custom.handler.oca"]
    _description = "Sales Book Report Custom Handler"
