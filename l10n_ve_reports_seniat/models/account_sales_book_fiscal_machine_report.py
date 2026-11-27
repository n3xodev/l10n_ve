# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class SalesBookFiscalMachineReportCustomHandler(models.AbstractModel):
    _name = "account.sales.book.fiscal.machine.report.handler.oca"
    _inherit = [
        "l10n.ve.sales.book.fiscal.machine.mixin",
        "account.report.custom.handler.oca",
    ]
    _description = "Sales Book Fiscal Machine Report Custom Handler"
