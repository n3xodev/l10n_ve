# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class L10nVeSalesBookFiscalMachineReportHandler(models.AbstractModel):
    _name = "l10n_ve.sales.book.fiscal.machine.report.handler"
    _inherit = [
        "l10n.ve.sales.book.fiscal.machine.mixin",
        "l10n.ve.enterprise.report.handler.mixin",
    ]
    _description = "Venezuela Enterprise Sales Book Fiscal Machine Report Handler"
