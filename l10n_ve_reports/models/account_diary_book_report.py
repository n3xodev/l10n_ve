# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class DiaryBookReportCustomHandler(models.AbstractModel):
    _name = "account.diary.book.report.handler.oca"
    _inherit = ["l10n.ve.diary.book.mixin", "account.report.custom.handler.oca"]
    _description = "Diary Book Report Custom Handler"
