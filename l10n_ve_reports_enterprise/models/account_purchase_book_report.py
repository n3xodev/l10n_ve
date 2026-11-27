# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class L10nVePurchaseBookReportHandler(models.AbstractModel):
    _name = "l10n_ve.purchase.book.report.handler"
    _inherit = [
        "l10n.ve.purchase.book.mixin",
        "l10n.ve.enterprise.report.handler.mixin",
    ]
    _description = "Venezuela Enterprise Purchase Book Report Handler"
