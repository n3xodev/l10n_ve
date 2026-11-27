# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from datetime import timedelta

from odoo import fields, models
from odoo.fields import Domain
from odoo.tools.float_utils import float_is_zero


class L10nVeInventoryBookMixin(models.AbstractModel):
    _name = "l10n.ve.inventory.book.mixin"
    _inherit = ["l10n.ve.report.adapter.mixin"]
    _description = "Shared mixin for Venezuelan SENIAT stock inventory book report"

    def _get_custom_display_config(self):
        return {
            "css_custom_class": "inventory_book_report",
        }

    def _custom_options_initializer(self, report, options, previous_options):
        super()._custom_options_initializer(
            report, options, previous_options=previous_options
        )
        options["multi_currency"] = report.env.user.has_group(
            "base.group_multi_currency"
        )
        options["warehouse_ids"] = (previous_options or {}).get("warehouse_ids", [])
        options["hide_zero_quantity_products"] = (previous_options or {}).get(
            "hide_zero_quantity_products", False
        )

    def _get_warehouses(self, options):
        warehouse_ids = options.get("warehouse_ids", [])
        warehouses = self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.company.id)]
        )
        if warehouse_ids:
            warehouses = warehouses.filtered(lambda w: w.id in warehouse_ids)
        return warehouses

    def _get_product_cost_currency(self, product):
        if hasattr(product, "cost_currency_id") and product.cost_currency_id:
            return product.cost_currency_id
        if hasattr(product, "product_tmpl_id") and hasattr(
            product.product_tmpl_id, "cost_currency_id"
        ):
            if product.product_tmpl_id.cost_currency_id:
                return product.product_tmpl_id.cost_currency_id
        return self.env.company.currency_id

    def _convert_to_display_currency(
        self, value, source_currency, options, date=None
    ):
        display_currency_id = options.get("display_currency_id")
        if not display_currency_id or source_currency.id == display_currency_id:
            return value, source_currency
        display_currency = self._l10n_ve_get_display_currency(options)
        if not date:
            currency_rate_date_type = options.get(
                "currency_rate_date_type", "current"
            )
            if currency_rate_date_type == "manual":
                date = options.get("currency_rate_date") or fields.Date.today()
            elif currency_rate_date_type == "document":
                date = (
                    options.get("date", {}).get("date_to") or fields.Date.today()
                )
            else:
                date = fields.Date.today()
        if isinstance(date, str):
            date = fields.Date.from_string(date)
        try:
            converted = source_currency._convert(
                value, display_currency, self.env.company, date
            )
            return converted, display_currency
        except Exception:
            return value, source_currency

    def _get_product_data(self, warehouses, date_from, date_to, company_currency):
        stock_location_ids = []
        for wh in warehouses:
            if wh.lot_stock_id and wh.lot_stock_id.parent_path:
                stock_locs = self.env["stock.location"].search(
                    [
                        "|",
                        ("id", "=", wh.lot_stock_id.id),
                        (
                            "parent_path",
                            "like",
                            wh.lot_stock_id.parent_path + "%",
                        ),
                    ]
                )
                stock_location_ids.extend(stock_locs.ids)
            elif wh.lot_stock_id:
                stock_location_ids.append(wh.lot_stock_id.id)

        retiros_location_ids = []
        autoconsumos_location_ids = []
        for wh in warehouses:
            if wh.l10n_ve_location_retiros_id:
                loc = wh.l10n_ve_location_retiros_id
                if loc.parent_path:
                    retiros_locs = self.env["stock.location"].search(
                        [
                            "|",
                            ("id", "=", loc.id),
                            ("parent_path", "like", loc.parent_path + "%"),
                        ]
                    )
                    retiros_location_ids.extend(retiros_locs.ids)
                else:
                    retiros_location_ids.append(loc.id)
            if wh.l10n_ve_location_autoconsumos_id:
                loc = wh.l10n_ve_location_autoconsumos_id
                if loc.parent_path:
                    autoconsumos_locs = self.env["stock.location"].search(
                        [
                            "|",
                            ("id", "=", loc.id),
                            ("parent_path", "like", loc.parent_path + "%"),
                        ]
                    )
                    autoconsumos_location_ids.extend(autoconsumos_locs.ids)
                else:
                    autoconsumos_location_ids.append(loc.id)

        Move = self.env["stock.move"].with_context(active_test=False)
        date_to_end = date_to + timedelta(days=1)
        move_domain = [
            ("state", "=", "done"),
            ("product_id.is_storable", "=", True),
            ("date", "<", fields.Datetime.to_string(date_to_end)),
        ]
        if stock_location_ids:
            move_domain = Domain.AND(
                [
                    move_domain,
                    [
                        "|",
                        ("location_id", "in", stock_location_ids),
                        ("location_dest_id", "in", stock_location_ids),
                    ],
                ]
            )

        moves = Move.search(move_domain)
        product_ids = moves.mapped("product_id").ids
        products = (
            self.env["product.product"]
            .browse(sorted(set(product_ids)))
            .filtered("is_storable")
        )

        result = defaultdict(
            lambda: {
                "inv_initial_qty": 0.0,
                "inv_initial_val": 0.0,
                "entradas_qty": 0.0,
                "entradas_val": 0.0,
                "salidas_qty": 0.0,
                "salidas_val": 0.0,
                "retiros_qty": 0.0,
                "retiros_val": 0.0,
                "autoconsumos_qty": 0.0,
                "autoconsumos_val": 0.0,
                "inv_final_qty": 0.0,
                "inv_final_val": 0.0,
                "cost": 0.0,
            }
        )

        for product in products:
            cost = product.standard_price or 0.0
            result[product.id]["cost"] = cost

        for move in moves:
            product = move.product_id
            if not product.is_storable:
                continue
            qty = move.product_qty
            cost = product.standard_price or 0.0
            val = qty * cost

            from_stock = move.location_id.id in stock_location_ids
            to_stock = move.location_dest_id.id in stock_location_ids
            to_retiros = move.location_dest_id.id in retiros_location_ids
            to_autoconsumos = move.location_dest_id.id in autoconsumos_location_ids

            move_date = move.date
            if hasattr(move_date, "date"):
                move_date = move_date.date()
            elif isinstance(move_date, str):
                move_date = fields.Date.from_string(move_date)

            if move_date < date_from:
                if to_stock and not from_stock:
                    result[product.id]["inv_initial_qty"] += qty
                    result[product.id]["inv_initial_val"] += val
                elif from_stock and not to_stock:
                    result[product.id]["inv_initial_qty"] -= qty
                    result[product.id]["inv_initial_val"] -= val
            elif date_from <= move_date <= date_to:
                if to_stock and not from_stock:
                    result[product.id]["entradas_qty"] += qty
                    result[product.id]["entradas_val"] += val
                elif from_stock and not to_stock:
                    if to_retiros:
                        result[product.id]["retiros_qty"] += qty
                        result[product.id]["retiros_val"] += val
                    elif to_autoconsumos:
                        result[product.id]["autoconsumos_qty"] += qty
                        result[product.id]["autoconsumos_val"] += val
                    else:
                        result[product.id]["salidas_qty"] += qty
                        result[product.id]["salidas_val"] += val

        for product in products:
            data = result[product.id]
            cost = product.standard_price or 0.0
            data["inv_initial_val"] = data["inv_initial_qty"] * cost
            inv_final = data["inv_initial_qty"] + data["entradas_qty"]
            inv_final -= data["salidas_qty"]
            inv_final -= data["retiros_qty"]
            inv_final -= data["autoconsumos_qty"]
            data["inv_final_qty"] = inv_final
            data["inv_final_val"] = inv_final * cost

        return result

    def _dynamic_lines_generator(
        self, report, options, all_column_groups_expression_totals, warnings=None
    ):
        lines = []
        date_from = options.get("date", {}).get("date_from")
        date_to = options.get("date", {}).get("date_to")
        if not date_from or not date_to:
            return lines

        date_from = fields.Date.from_string(date_from)
        date_to = fields.Date.from_string(date_to)

        warehouses = self._get_warehouses(options)
        if not warehouses:
            return lines

        company_currency = self.env.company.currency_id
        product_data = self._get_product_data(
            warehouses, date_from, date_to, company_currency
        )

        totals = {
            "inv_initial_qty": 0.0,
            "inv_initial_val": 0.0,
            "entradas_qty": 0.0,
            "entradas_val": 0.0,
            "salidas_qty": 0.0,
            "salidas_val": 0.0,
            "retiros_qty": 0.0,
            "retiros_val": 0.0,
            "autoconsumos_qty": 0.0,
            "autoconsumos_val": 0.0,
            "inv_final_qty": 0.0,
            "inv_final_val": 0.0,
        }

        display_currency = self._l10n_ve_get_display_currency(options)
        date_to_conv = options.get("date", {}).get("date_to") or fields.Date.today()
        if isinstance(date_to_conv, str):
            date_to_conv = fields.Date.from_string(date_to_conv)

        qty_fields = (
            "inv_initial_qty",
            "entradas_qty",
            "salidas_qty",
            "retiros_qty",
            "autoconsumos_qty",
            "inv_final_qty",
        )
        for product_id, data in sorted(product_data.items()):
            product = self.env["product.product"].browse(product_id)
            if not product.exists():
                continue
            if not product.active:
                continue
            if options.get("hide_zero_quantity_products"):
                if all(
                    float_is_zero(
                        data[field_name],
                        precision_rounding=product.uom_id.rounding or 0.01,
                    )
                    for field_name in qty_fields
                ):
                    continue

            cost_currency = self._get_product_cost_currency(product)
            conv_cost, _ = self._convert_to_display_currency(
                data["cost"], cost_currency, options, date_to_conv
            )
            conv_inv_initial, _ = self._convert_to_display_currency(
                data["inv_initial_val"], cost_currency, options, date_to_conv
            )
            conv_entradas, _ = self._convert_to_display_currency(
                data["entradas_val"], cost_currency, options, date_to_conv
            )
            conv_salidas, _ = self._convert_to_display_currency(
                data["salidas_val"], cost_currency, options, date_to_conv
            )
            conv_retiros, _ = self._convert_to_display_currency(
                data["retiros_val"], cost_currency, options, date_to_conv
            )
            conv_autoconsumos, _ = self._convert_to_display_currency(
                data["autoconsumos_val"], cost_currency, options, date_to_conv
            )
            conv_inv_final, _ = self._convert_to_display_currency(
                data["inv_final_val"], cost_currency, options, date_to_conv
            )

            line_columns = []
            for column in options["columns"]:
                col_expr_label = column.get("expression_label", "")
                if col_expr_label == "code":
                    val = product.default_code or str(product.id)
                    line_columns.append(
                        self._l10n_ve_build_column(report, val, column, options)
                    )
                elif col_expr_label == "product":
                    line_columns.append(
                        self._l10n_ve_build_column(
                            report, product.display_name, column, options
                        )
                    )
                elif col_expr_label == "cost":
                    line_columns.append(
                        self._l10n_ve_build_column(
                            report,
                            conv_cost,
                            column,
                            options,
                            currency=display_currency,
                        )
                    )
                elif col_expr_label == "inv_initial_qty":
                    line_columns.append(
                        self._l10n_ve_build_column(
                            report, data["inv_initial_qty"], column, options
                        )
                    )
                elif col_expr_label == "inv_initial_val":
                    line_columns.append(
                        self._l10n_ve_build_column(
                            report,
                            conv_inv_initial,
                            column,
                            options,
                            currency=display_currency,
                        )
                    )
                elif col_expr_label == "entradas_qty":
                    line_columns.append(
                        self._l10n_ve_build_column(
                            report, data["entradas_qty"], column, options
                        )
                    )
                elif col_expr_label == "entradas_val":
                    line_columns.append(
                        self._l10n_ve_build_column(
                            report,
                            conv_entradas,
                            column,
                            options,
                            currency=display_currency,
                        )
                    )
                elif col_expr_label == "salidas_qty":
                    line_columns.append(
                        self._l10n_ve_build_column(
                            report, data["salidas_qty"], column, options
                        )
                    )
                elif col_expr_label == "salidas_val":
                    line_columns.append(
                        self._l10n_ve_build_column(
                            report,
                            conv_salidas,
                            column,
                            options,
                            currency=display_currency,
                        )
                    )
                elif col_expr_label == "retiros_qty":
                    line_columns.append(
                        self._l10n_ve_build_column(
                            report, data["retiros_qty"], column, options
                        )
                    )
                elif col_expr_label == "retiros_val":
                    line_columns.append(
                        self._l10n_ve_build_column(
                            report,
                            conv_retiros,
                            column,
                            options,
                            currency=display_currency,
                        )
                    )
                elif col_expr_label == "autoconsumos_qty":
                    line_columns.append(
                        self._l10n_ve_build_column(
                            report, data["autoconsumos_qty"], column, options
                        )
                    )
                elif col_expr_label == "autoconsumos_val":
                    line_columns.append(
                        self._l10n_ve_build_column(
                            report,
                            conv_autoconsumos,
                            column,
                            options,
                            currency=display_currency,
                        )
                    )
                elif col_expr_label == "inv_final_qty":
                    line_columns.append(
                        self._l10n_ve_build_column(
                            report, data["inv_final_qty"], column, options
                        )
                    )
                elif col_expr_label == "inv_final_val":
                    line_columns.append(
                        self._l10n_ve_build_column(
                            report,
                            conv_inv_final,
                            column,
                            options,
                            currency=display_currency,
                        )
                    )
                else:
                    line_columns.append(
                        self._l10n_ve_build_column(report, None, column, options)
                    )

            totals["inv_initial_qty"] += data["inv_initial_qty"]
            totals["inv_initial_val"] += conv_inv_initial
            totals["entradas_qty"] += data["entradas_qty"]
            totals["entradas_val"] += conv_entradas
            totals["salidas_qty"] += data["salidas_qty"]
            totals["salidas_val"] += conv_salidas
            totals["retiros_qty"] += data["retiros_qty"]
            totals["retiros_val"] += conv_retiros
            totals["autoconsumos_qty"] += data["autoconsumos_qty"]
            totals["autoconsumos_val"] += conv_autoconsumos
            totals["inv_final_qty"] += data["inv_final_qty"]
            totals["inv_final_val"] += conv_inv_final

            line_id = report._get_generic_line_id(None, "product.product", product_id)
            lines.append(
                (
                    0,
                    self._l10n_ve_build_line(
                        {
                            "id": line_id,
                            "name": product.display_name,
                            "columns": line_columns,
                            "level": 2,
                            "unfoldable": False,
                            "caret_options": None,
                        }
                    ),
                )
            )

        if product_data:
            total_columns = []
            for column in options["columns"]:
                col_expr_label = column.get("expression_label", "")
                if col_expr_label == "code":
                    total_columns.append(
                        self._l10n_ve_build_column(report, "", column, options)
                    )
                elif col_expr_label == "product":
                    total_columns.append(
                        self._l10n_ve_build_column(
                            report, "TOTALES DEL PERIODO", column, options
                        )
                    )
                elif col_expr_label == "cost":
                    total_columns.append(
                        self._l10n_ve_build_column(report, None, column, options)
                    )
                elif "val" in col_expr_label and col_expr_label in totals:
                    total_columns.append(
                        self._l10n_ve_build_column(
                            report,
                            totals[col_expr_label],
                            column,
                            options,
                            currency=display_currency,
                        )
                    )
                elif col_expr_label in totals:
                    total_columns.append(
                        self._l10n_ve_build_column(
                            report, totals[col_expr_label], column, options
                        )
                    )
                else:
                    total_columns.append(
                        self._l10n_ve_build_column(report, None, column, options)
                    )

            lines.append(
                (
                    0,
                    self._l10n_ve_build_line(
                        {
                            "id": report._get_generic_line_id(
                                None, "inventory_book_totals", 0
                            ),
                            "name": "TOTALES DEL PERIODO",
                            "columns": total_columns,
                            "level": 2,
                            "unfoldable": False,
                            "caret_options": None,
                        }
                    ),
                )
            )

        return lines
