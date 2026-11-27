# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class L10nVeLiquidityBookReportMixin(models.AbstractModel):
    _name = "l10n.ve.liquidity.book.report.mixin"
    _inherit = ["l10n.ve.liquidity.book.mixin", "account.report.custom.handler.oca"]
    _description = "Mixin for Venezuelan bank and cash auxiliary books"
