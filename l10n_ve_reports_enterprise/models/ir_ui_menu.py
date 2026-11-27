# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    @api.model
    def _l10n_ve_emission_medium_menu_rules(self):
        rules = dict(super()._l10n_ve_emission_medium_menu_rules())
        rules["fiscal_machine"] = rules.get("fiscal_machine", ()) + (
            "l10n_ve_reports_enterprise.menu_seniat_report_sales_book_fiscal_machine",
        )
        return rules
