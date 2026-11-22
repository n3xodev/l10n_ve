from odoo import api, models


class AccountJournal(models.Model):
    _name = "account.journal"
    _inherit = ["account.journal", "pos.load.mixin"]

    @api.model
    def _load_pos_data_domain(self, data):
        return [
            *self._check_company_domain(data["pos.config"].company_id),
            ("type", "=", "sale"),
        ]

    @api.model
    def _load_pos_data_dependencies(self):
        return ["pos.config"]

    @api.model
    def _load_pos_data_fields(self, config):
        return [
            "id",
            "name",
            "display_name",
            "code",
            "type",
            "currency_id",
            "company_id",
            "l10n_ve_emission_medium",
        ]
