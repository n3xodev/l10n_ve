# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models
from odoo.addons.account_reports.models.account_report import CURRENCIES_USING_LAKH
from odoo.addons.account_reports.utils.report_data_objects import (
    AccountReportColumnFormatParamsData,
)


class AccountReport(models.Model):
    _inherit = "account.report"

    ####################################################
    # OPTIONS: DISPLAY CURRENCY
    ####################################################

    def _get_options_initializers_forced_sequence_map(self):
        sequence_map = super()._get_options_initializers_forced_sequence_map()
        sequence_map[self._init_options_display_currency] = 35
        return sequence_map

    def _init_options_display_currency(self, options, previous_options):
        """Initialize the display currency selector options."""
        previous_options = previous_options or {}
        company_currency_id = self.env.company.currency_id.id
        display_currency_id = previous_options.get(
            "display_currency_id", company_currency_id
        )

        currency = self.env["res.currency"].browse(display_currency_id).exists()
        if not currency or not currency.active:
            display_currency_id = company_currency_id
            currency = self.env["res.currency"].browse(display_currency_id)

        options["display_currency_id"] = display_currency_id
        options["display_currency"] = currency.read(["id", "name", "symbol"])[0]

        available_currencies = self.env["res.currency"].search([("active", "=", True)])
        options["available_currencies"] = available_currencies.read(
            ["id", "name", "symbol"]
        )

        currency_rate_date_type = previous_options.get(
            "currency_rate_date_type", "current"
        )
        if currency_rate_date_type not in ("current", "document", "manual"):
            currency_rate_date_type = "current"
        options["currency_rate_date_type"] = currency_rate_date_type

        if currency_rate_date_type == "manual":
            currency_rate_date = previous_options.get("currency_rate_date")
            if currency_rate_date:
                try:
                    parsed_date = fields.Date.from_string(currency_rate_date)
                except (ValueError, TypeError):
                    parsed_date = fields.Date.today()
                options["currency_rate_date"] = fields.Date.to_string(parsed_date)
            else:
                options["currency_rate_date"] = fields.Date.to_string(
                    fields.Date.today()
                )
        else:
            options["currency_rate_date"] = None

    ####################################################
    # OPTIONS: ROUNDING UNIT
    ####################################################

    def _init_options_rounding_unit(self, options, previous_options):
        super()._init_options_rounding_unit(options, previous_options)
        display_currency_id = options.get(
            "display_currency_id", self.env.company.currency_id.id
        )
        options["rounding_unit_names"] = self._get_rounding_unit_names(
            currency=display_currency_id
        )

    def _get_rounding_unit_names(self, currency=None):
        if currency is None:
            currency = self.env.company.currency_id
        elif isinstance(currency, int):
            currency = self.env["res.currency"].browse(currency)

        currency_symbol = currency.symbol
        currency_name = currency.name
        rounding_unit_names = [
            ("decimals", f".{currency_symbol}"),
            ("units", f"{currency_symbol}"),
            ("thousands", f"k{currency_symbol}"),
            ("millions", f"M{currency_symbol}"),
        ]
        if currency_name in CURRENCIES_USING_LAKH:
            rounding_unit_names.insert(3, ("lakhs", f"L{currency_symbol}"))
        return dict(rounding_unit_names)

    ####################################################
    # FORMATTING & CURRENCY CONVERSION
    ####################################################

    def _get_document_dates_for_lines(self, line_data_list):
        """Extract document dates for lines to support per-document currency conversion."""
        document_dates = {}
        aml_ids_map = {}
        move_ids_map = {}

        for line_data in line_data_list:
            line_id = line_data.id or ""
            doc_date = None
            for col in line_data.columns or ():
                if (
                    col
                    and col.expression_label in ("invoice_date", "date")
                    and col.no_format
                ):
                    doc_date = col.no_format
                    break

            if doc_date:
                document_dates[line_id] = doc_date
            elif line_id:
                aml_id = self._get_res_id_from_line_id(line_id, "account.move.line")
                if aml_id:
                    aml_ids_map[line_id] = aml_id
                else:
                    move_id = self._get_res_id_from_line_id(line_id, "account.move")
                    if move_id:
                        move_ids_map[line_id] = move_id

        if aml_ids_map:
            amls = self.env["account.move.line"].browse(list(set(aml_ids_map.values())))
            aml_dates = {
                aml.id: aml.move_id.invoice_date or aml.date for aml in amls
            }
            for line_id, aml_id in aml_ids_map.items():
                if aml_id in aml_dates:
                    document_dates[line_id] = aml_dates[aml_id]

        if move_ids_map:
            moves = self.env["account.move"].browse(list(set(move_ids_map.values())))
            move_dates = {
                move.id: move.invoice_date or move.date for move in moves
            }
            for line_id, move_id in move_ids_map.items():
                if move_id in move_dates:
                    document_dates[line_id] = move_dates[move_id]

        return document_dates

    def _precompute_grouped_line_converted_values(
        self, options, line_data_list, document_dates
    ):
        """Precompute converted monetary totals for folded/grouped lines in document-date mode."""
        currency_rate_date_type = options.get("currency_rate_date_type", "current")
        display_currency_id = options.get("display_currency_id")
        if (
            currency_rate_date_type != "document"
            or not display_currency_id
            or options.get("export_mode") == "file"
        ):
            return

        company_currency = self.env.company.currency_id
        if display_currency_id == company_currency.id:
            return

        display_currency = self.env["res.currency"].browse(display_currency_id)

        for line_data in line_data_list:
            line_id = line_data.id or ""
            if line_id in document_dates:
                continue

            if (
                not line_data.unfoldable
                or not line_data.groupby
                or line_data.expand_function
                != "_report_expand_unfoldable_line_with_groupby"
            ):
                continue

            try:
                child_lines = self._report_expand_unfoldable_line_with_groupby(
                    line_id,
                    line_data.groupby,
                    options,
                )
            except Exception:
                continue

            if not child_lines:
                continue

            child_doc_dates = self._get_document_dates_for_lines(child_lines)
            self._precompute_grouped_line_converted_values(
                options, child_lines, child_doc_dates
            )

            for col_idx, parent_col in enumerate(line_data.columns or ()):
                if not parent_col or parent_col.figure_type != "monetary":
                    continue
                if parent_col.no_format is None:
                    continue

                parent_currency_id = (
                    parent_col.format_params.currency_id
                    if parent_col.format_params
                    else None
                )
                if parent_currency_id and parent_currency_id != company_currency.id:
                    continue

                converted_total = 0.0
                has_child_values = False

                for child in child_lines:
                    child_cols = child.columns or ()
                    if col_idx >= len(child_cols):
                        continue
                    child_col = child_cols[col_idx]
                    if not child_col or child_col.no_format is None:
                        continue

                    has_child_values = True
                    child_value = child_col.no_format
                    if child_value == 0:
                        continue

                    child_source_currency_id = (
                        child_col.format_params.currency_id
                        if child_col.format_params
                        else None
                    )
                    source_currency = (
                        self.env["res.currency"].browse(child_source_currency_id)
                        if child_source_currency_id
                        else company_currency
                    )

                    if source_currency.id == display_currency_id:
                        converted_total += child_value
                    elif source_currency.id == company_currency.id:
                        doc_date = (
                            child_doc_dates.get(child.id or "")
                            or options.get("date", {}).get("date_to")
                            or fields.Date.today()
                        )
                        if isinstance(doc_date, str):
                            doc_date = fields.Date.from_string(doc_date)
                        converted_total += source_currency._convert(
                            child_value,
                            display_currency,
                            self.env.company,
                            doc_date,
                        )
                    else:
                        converted_total += child_value

                if has_child_values:
                    digits = (
                        parent_col.format_params.digits
                        if parent_col.format_params
                        else None
                    )
                    new_format_params = AccountReportColumnFormatParamsData(
                        currency_id=display_currency_id,
                        digits=digits,
                    )
                    parent_col.no_format = converted_total
                    parent_col.format_params = new_format_params
                    parent_col.currency = display_currency
                    parent_col.is_zero = self._is_value_zero(
                        converted_total, "monetary", new_format_params
                    )

    def _format_column_values(self, options, line_data_list, force_format=False):
        display_currency_id = (options or {}).get("display_currency_id")
        company_currency = self.env.company.currency_id

        if not display_currency_id or display_currency_id == company_currency.id:
            return super()._format_column_values(
                options, line_data_list, force_format=force_format
            )

        display_currency = self.env["res.currency"].browse(display_currency_id)
        currency_rate_date_type = options.get("currency_rate_date_type", "current")
        document_dates = {}

        if currency_rate_date_type == "document":
            document_dates = self._get_document_dates_for_lines(line_data_list)
            self._precompute_grouped_line_converted_values(
                options, line_data_list, document_dates
            )

        for line_data in line_data_list:
            line_document_date = (
                document_dates.get(line_data.id or "")
                if currency_rate_date_type == "document"
                else None
            )
            precomputed_cols = any(
                col
                and col.figure_type == "monetary"
                and col.format_params
                and col.format_params.currency_id == display_currency_id
                for col in (line_data.columns or ())
            )
            super(
                AccountReport,
                self.with_context(l10n_ve_document_date=line_document_date),
            )._format_column_values(options, [line_data], force_format=force_format)

            if (
                precomputed_cols
                and line_data.horizontal_group_total_data
                and line_data.horizontal_group_total_data.figure_type == "monetary"
                and line_data.horizontal_group_total_data.no_format is not None
            ):
                total_col = line_data.horizontal_group_total_data
                total_params = AccountReportColumnFormatParamsData(
                    currency_id=display_currency_id,
                    digits=total_col.format_params.digits
                    if total_col.format_params
                    else None,
                )
                total_col.format_params = total_params
                total_col.currency = display_currency
                if options.get("multi_currency"):
                    total_col.currency_symbol = display_currency.symbol
                total_col.name = self._format_value(
                    options,
                    total_col.no_format,
                    "monetary",
                    format_params=total_params,
                )

            for col in line_data.columns or ():
                if not col or col.figure_type != "monetary" or col.no_format is None:
                    continue
                source_currency_id = (
                    col.format_params.currency_id if col.format_params else None
                )
                if not source_currency_id or source_currency_id == company_currency.id:
                    col.currency = display_currency
                    if options.get("multi_currency"):
                        col.currency_symbol = display_currency.symbol

    def _resolve_display_currency_rate_date(self, options):
        currency_rate_date_type = (options or {}).get(
            "currency_rate_date_type", "current"
        )
        if currency_rate_date_type == "manual":
            rate_date = options.get("currency_rate_date") or fields.Date.today()
        elif currency_rate_date_type == "document":
            rate_date = (
                self.env.context.get("l10n_ve_document_date")
                or options.get("date", {}).get("date_to")
                or fields.Date.today()
            )
        else:
            rate_date = fields.Date.today()

        if isinstance(rate_date, str):
            rate_date = fields.Date.from_string(rate_date)
        return rate_date

    def _format_value(self, options, value, figure_type, format_params=None):
        if (
            figure_type == "monetary"
            and value is not None
            and not isinstance(value, str)
            and options
        ):
            display_currency_id = options.get("display_currency_id")
            company_currency = self.env.company.currency_id
            if display_currency_id:
                source_currency_id = (
                    format_params.currency_id if format_params else None
                )
                source_currency = (
                    self.env["res.currency"].browse(source_currency_id)
                    if source_currency_id
                    else company_currency
                )
                if (
                    display_currency_id != source_currency.id
                    and source_currency.id == company_currency.id
                ):
                    display_currency = self.env["res.currency"].browse(
                        display_currency_id
                    )
                    rate_date = self._resolve_display_currency_rate_date(options)
                    value = source_currency._convert(
                        value,
                        display_currency,
                        self.env.company,
                        rate_date,
                    )
                    format_params = AccountReportColumnFormatParamsData(
                        currency_id=display_currency.id,
                        digits=format_params.digits if format_params else None,
                    )
        return super()._format_value(
            options, value, figure_type, format_params=format_params
        )
