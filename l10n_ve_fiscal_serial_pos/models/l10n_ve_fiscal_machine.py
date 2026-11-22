# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class L10nVeFiscalMachine(models.Model):
    _name = "l10n.ve.fiscal.machine"
    _inherit = ["l10n.ve.fiscal.machine", "pos.load.mixin"]

    @api.model
    def _load_pos_data_domain(self, data):
        return [
            ("company_id", "=", data["pos.config"].company_id.id),
            ("active", "=", True),
        ]

    @api.model
    def _load_pos_data_dependencies(self):
        return ["pos.config"]

    @api.model
    def _load_pos_data_fields(self, config):
        return [
            "id",
            "name",
            "registered_serial",
            "serial_port",
            "baudrate",
            "parity",
            "webserial_usb_vendor_id",
            "webserial_usb_product_id",
            "webserial_usb_serial_number",
            "last_invoice_number",
            "last_credit_note_number",
            "last_debit_note_number",
            "daily_closure_counter",
            "use_emulator",
            "send_default_code_in_name",
        ]
