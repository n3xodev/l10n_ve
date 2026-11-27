# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class L10nVeSalesBookReportHandler(models.AbstractModel):
    _name = "l10n_ve.sales.book.report.handler"
    _inherit = [
        "l10n.ve.sales.book.mixin",
        "l10n.ve.enterprise.report.handler.mixin",
    ]
    _description = "Venezuela Enterprise Sales Book Report Handler"
