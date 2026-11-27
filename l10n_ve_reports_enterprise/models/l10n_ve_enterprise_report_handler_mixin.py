# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models
from odoo.addons.account_reports.utils.report_data_objects import (
    AccountReportColumnData,
    AccountReportLineData,
)


class L10nVeEnterpriseReportHandlerMixin(models.AbstractModel):
    _name = "l10n.ve.enterprise.report.handler.mixin"
    _inherit = [
        "l10n.ve.report.adapter.mixin",
        "account.report.custom.handler",
    ]
    _description = "Enterprise account_reports adapter mixin for Venezuelan reports"

    def _l10n_ve_build_column(
        self,
        report,
        value,
        column,
        options,
        currency=None,
        digits=1,
        column_expression=None,
        has_sublines=False,
        report_line_id=None,
    ):
        return report._build_column_data(
            value,
            column,
            options=options,
            currency=currency or False,
            digits=digits,
            column_expression=column_expression,
            has_sublines=has_sublines,
            report_line_id=report_line_id,
        )

    def _l10n_ve_build_line(self, line_dict):
        data = dict(line_dict)
        raw_columns = data.pop("columns", [])
        line = AccountReportLineData.from_dict(data)
        line.columns = [
            AccountReportColumnData.from_dict(col) if isinstance(col, dict) else col
            for col in raw_columns
        ]
        return line
