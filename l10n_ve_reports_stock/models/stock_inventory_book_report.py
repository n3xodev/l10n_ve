# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class StockInventoryBookReportHandler(models.AbstractModel):
    _name = "stock.inventory.book.report.handler.oca"
    _inherit = ["l10n.ve.inventory.book.mixin", "account.report.custom.handler.oca"]
    _description = "Stock Inventory Book Report Handler"

    def _get_custom_display_config(self):
        return {
            **super()._get_custom_display_config(),
            "components": {
                "AccountReportFilters": "l10n_ve_reports_stock.InventoryBookReportFilters",
            },
        }
