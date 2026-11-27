# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class L10nVeReportAdapterMixin(models.AbstractModel):
    _name = "l10n.ve.report.adapter.mixin"
    _description = "Edition-agnostic adapter mixin for Venezuelan accounting reports"

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
        """Build a report column entry compatible with both CE and EE engines."""
        resolved_currency = currency or False
        if hasattr(report, "_build_column_data"):
            return report._build_column_data(
                value,
                column,
                options=options,
                currency=resolved_currency,
                digits=digits,
                column_expression=column_expression,
                has_sublines=has_sublines,
                report_line_id=report_line_id,
            )
        return report._build_column_dict(
            value,
            column,
            options=options,
            currency=resolved_currency,
            digits=digits,
            column_expression=column_expression,
            has_sublines=has_sublines,
            report_line_id=report_line_id,
        )

    def _l10n_ve_build_line(self, line_dict):
        """Return a report line structure (dict in CE, overridden in EE)."""
        return line_dict

    def _l10n_ve_get_column_group_keys(self, options):
        """Return hashable column-group identifiers for both CE (dict) and EE (list)."""
        column_groups = (options or {}).get("column_groups") or {}
        if isinstance(column_groups, dict):
            return list(column_groups.keys())
        return list(range(len(column_groups)))

    def _l10n_ve_get_column_group_key(self, column):
        """Return the hashable column-group identifier for a column descriptor."""
        if "column_group_key" in column:
            return column["column_group_key"]
        return column.get("column_group_index", 0)

    def _l10n_ve_get_display_currency(self, options):
        """Return the active display currency, falling back to company currency."""
        currency_id = (options or {}).get("display_currency_id")
        return self.env["res.currency"].browse(
            currency_id or self.env.company.currency_id.id
        )

    def _l10n_ve_to_report_date(self, value):
        if not value:
            return False
        if isinstance(value, str):
            return fields.Date.from_string(value)
        return value

    def _l10n_ve_get_report_date_bounds(self, options):
        date_info = options["date"]
        date_to = self._l10n_ve_to_report_date(date_info["date_to"])
        if date_info.get("mode") == "single":
            if date_info.get("period_type") == "today":
                return date_to, date_to
            date_from = self._l10n_ve_to_report_date(date_info.get("date_from"))
            if date_from:
                return date_from, date_to
            return date_to, date_to
        date_from = self._l10n_ve_to_report_date(date_info.get("date_from"))
        if not date_from:
            return date_to, date_to
        return date_from, date_to

    def _l10n_ve_export_to_pdf_landscape(self, options):
        report = self.env["account.report"].browse(options["report_id"])
        return type(report).export_to_pdf(
            report.with_context(force_landscape_printing=True), options
        )
