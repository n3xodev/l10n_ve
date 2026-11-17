from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    is_retention = fields.Boolean(
        string="Is retention",
        help="Check this box if this payment is a retention",
        copy=False,
    )
    l10n_ve_process_date = fields.Date(
        string="Fecha de proceso",
        copy=False,
        tracking=True,
    )

    def _l10n_ve_sync_process_date_to_move(self):
        for payment in self.filtered("l10n_ve_process_date"):
            move = payment.move_id
            if not move:
                continue
            if move.origin_payment_id and move.origin_payment_id != payment:
                continue
            move.l10n_ve_process_date = payment.l10n_ve_process_date

    def _l10n_ve_set_process_date_on_validation(self):
        today = fields.Date.context_today(self)
        validated = self.filtered(lambda pay: pay.state in ("paid", "reconciled"))
        for payment in validated.filtered(lambda pay: not pay.l10n_ve_process_date):
            payment.l10n_ve_process_date = today
        validated._l10n_ve_sync_process_date_to_move()
        for payment in validated:
            move = payment.move_id
            if move and not move.l10n_ve_process_date:
                move.l10n_ve_process_date = payment.l10n_ve_process_date

    def write(self, vals):
        res = super().write(vals)
        if "state" in vals:
            self._l10n_ve_set_process_date_on_validation()
        elif "l10n_ve_process_date" in vals:
            self._l10n_ve_sync_process_date_to_move()
        return res

    def action_draft(self):
        res = super().action_draft()
        self.write({"l10n_ve_process_date": False})
        return res
