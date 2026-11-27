# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class L10nVeDiaryBookReportHandler(models.AbstractModel):
    _name = "l10n_ve.diary.book.report.handler"
    _inherit = [
        "l10n.ve.diary.book.mixin",
        "l10n.ve.enterprise.report.handler.mixin",
    ]
    _description = "Venezuela Enterprise Diary Book Report Handler"
