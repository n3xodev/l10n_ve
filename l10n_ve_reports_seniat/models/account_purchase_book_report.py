# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class PurchaseBookReportCustomHandler(models.AbstractModel):
    _name = "account.purchase.book.report.handler.oca"
    _inherit = ["l10n.ve.purchase.book.mixin", "account.report.custom.handler.oca"]
    _description = "Purchase Book Report Custom Handler"
