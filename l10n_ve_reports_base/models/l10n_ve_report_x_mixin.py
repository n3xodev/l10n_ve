# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models
from odoo.tools.misc import format_date, format_datetime


class L10nVeReportXMixin(models.AbstractModel):
    _name = "l10n.ve.report.x.mixin"
    _inherit = ["l10n.ve.report.adapter.mixin"]
    _description = "Shared mixin for Venezuela Reporte X (consolidated summary)"

    def _custom_options_initializer(self, report, options, previous_options):
        super()._custom_options_initializer(
            report, options, previous_options=previous_options
        )
        options["unfold_all"] = options.get("unfold_all", True)

        if previous_options.get("is_opening_report"):
            today = fields.Date.context_today(report)
            date_opt = options.get("date")
            if not date_opt or date_opt.get("period_type") != "today":
                options["date"] = report._get_dates_period(
                    today, today, "single", period_type="today"
                )
            options["date"]["filter"] = "this_today"
            options["date"]["period"] = 0

    def _get_custom_display_config(self):
        return {
            "css_custom_class": "ve_report_x",
        }

    def _get_daily_payments_handler(self):
        raise NotImplementedError

    def _get_sales_book_handler(self):
        raise NotImplementedError

    def _daily(self):
        return self._get_daily_payments_handler()

    def _sales(self):
        return self._get_sales_book_handler()

    def _get_report_date_bounds(self, options):
        return self._daily()._get_report_date_bounds(options)

    def _amount_to_report_currency(self, amount_company, company, options, conv_date):
        return self._daily()._amount_to_report_currency(
            amount_company, company, options, conv_date
        )

    def _build_row_columns(self, report, options, values_map):
        display_currency = self._l10n_ve_get_display_currency(options)
        line_columns = []
        for column in options["columns"]:
            label = column["expression_label"]
            if label not in values_map:
                line_columns.append(
                    self._l10n_ve_build_column(report, None, column, options)
                )
                continue
            value = values_map[label]
            if column.get("figure_type") == "monetary":
                line_columns.append(
                    self._l10n_ve_build_column(
                        report,
                        value,
                        column,
                        options,
                        currency=display_currency,
                    )
                )
            else:
                line_columns.append(
                    self._l10n_ve_build_column(report, value, column, options)
                )
        return line_columns

    def _tax_values_for_move(self, move):
        sales = self._sales()
        if hasattr(move, "sale_tax_data") and move.sale_tax_data:
            return sales._get_tax_values_from_stored(move)
        return sales._calculate_tax_values(move)

    def _aggregate_tax_maps(self, moves, options=None):
        keys = (
            "total_exempt",
            "base_general",
            "amount_general",
            "base_reduced",
            "amount_reduced",
            "base_extend",
            "amount_extend",
            "total_taxed",
        )
        acc = {k: 0.0 for k in keys}
        for move in moves:
            tv = self._tax_values_for_move(move)
            conv_date = move.invoice_date or move.date
            for k in keys:
                val = tv.get(k, 0.0)
                if options is not None:
                    val = self._amount_to_report_currency(
                        val, move.company_id, options, conv_date
                    )
                acc[k] += val
        return acc

    def _invoice_domain_base(self, report, options, move_types):
        date_from, date_to = self._get_report_date_bounds(options)
        company_ids = report.get_report_company_ids(options)
        domain = [
            ("move_type", "in", move_types),
            ("state", "=", "posted"),
            ("date", ">=", date_from),
            ("date", "<=", date_to),
            ("company_id", "in", company_ids),
        ]
        journal_domain = report._get_options_journals_domain(options)
        if journal_domain:
            domain += journal_domain
        return domain

    def _move_type_in_selection(self, code):
        Move = self.env["account.move"]
        for key, _label in Move._fields["move_type"]._description_selection(Move.env):
            if key == code:
                return True
        return False

    def _search_sales_invoices_and_receipts(self, report, options):
        domain = self._invoice_domain_base(
            report, options, ("out_invoice", "out_receipt")
        )
        if "debit_origin_id" in self.env["account.move"]._fields:
            domain.append(("debit_origin_id", "=", False))
        return self.env["account.move"].search(domain, order="id asc")

    def _search_customer_debit_notes(self, report, options):
        date_from, date_to = self._get_report_date_bounds(options)
        company_ids = report.get_report_company_ids(options)
        domain = [
            ("state", "=", "posted"),
            ("date", ">=", date_from),
            ("date", "<=", date_to),
            ("company_id", "in", company_ids),
        ]
        journal_domain = report._get_options_journals_domain(options)
        if journal_domain:
            domain += journal_domain
        Move = self.env["account.move"]
        debit_notes = Move
        if self._move_type_in_selection("out_debit"):
            debit_notes = Move.search(
                domain + [("move_type", "=", "out_debit")], order="id asc"
            )
        if "debit_origin_id" in Move._fields:
            linked = Move.search(
                domain
                + [
                    ("move_type", "in", ("out_invoice", "out_receipt")),
                    ("debit_origin_id", "!=", False),
                ],
                order="id asc",
            )
            debit_notes |= linked
        return debit_notes

    def _cancel_move_types_customer(self):
        types = ["out_invoice", "out_refund", "out_receipt"]
        if self._move_type_in_selection("out_debit"):
            types.append("out_debit")
        return types

    def _discount_total_company(self, moves):
        total = 0.0
        for move in moves:
            company_currency = move.company_id.currency_id
            for line in move.invoice_line_ids:
                if line.display_type in ("line_section", "line_note"):
                    continue
                if not line.discount:
                    continue
                disc = line.discount
                if disc >= 100:
                    continue
                gross = line.price_subtotal / (1.0 - disc / 100.0)
                total += company_currency.round(gross - line.price_subtotal)
        return total

    def _discount_total_report_currency(self, moves, options):
        total = 0.0
        for move in moves:
            move_disc = self._discount_total_company(move)
            if move_disc:
                total += self._amount_to_report_currency(
                    move_disc,
                    move.company_id,
                    options,
                    move.invoice_date or move.date,
                )
        return total

    def _cancelled_total_report_currency(self, cancelled, options):
        total = 0.0
        for move in cancelled:
            total += self._amount_to_report_currency(
                move.amount_total_signed,
                move.company_id,
                options,
                move.invoice_date or move.date,
            )
        return total

    def _dynamic_lines_generator(
        self, report, options, all_column_groups_expression_totals, warnings=None
    ):
        lines = []
        date_from, date_to = self._get_report_date_bounds(options)
        company_ids = report.get_report_company_ids(options)
        if not company_ids:
            return []
        main_company = self.env["res.company"].browse(company_ids[0])
        gen_ts = format_datetime(
            self.env,
            fields.Datetime.now(),
            dt_format="dd/MM/yyyy HH:mm",
        )

        def add_row(name, detail, amount, level=1, line_class=None, markup="rx"):
            row_id = report._get_generic_line_id(
                None, None, markup=f"{markup}_{len(lines)}"
            )
            values_map = {
                "row_detail": detail or "",
                "row_amount": amount,
            }
            line = {
                "id": row_id,
                "name": name,
                "columns": self._build_row_columns(report, options, values_map),
                "level": level,
                "unfoldable": False,
            }
            if line_class:
                line["class"] = line_class
            lines.append((0, self._l10n_ve_build_line(line)))

        period_label = _("%(date_from)s — %(date_to)s") % {
            "date_from": format_date(self.env, date_from),
            "date_to": format_date(self.env, date_to),
        }
        add_row(_("Reporte X (resumen consolidado)"), period_label, None, level=0)
        add_row(_("Generado"), gen_ts, None, level=1)
        partner = main_company.partner_id
        if partner and partner.vat:
            add_row(_("RIF / identificación fiscal"), partner.vat, None, level=1)
        add_row(_("Usuario"), self.env.user.name, None, level=1)

        daily = self._daily()
        date_type = daily._get_daily_payments_date_type(options)
        bank_cash_journals = daily._get_selected_bank_cash_journals(report, options)
        add_row(
            _("Arqueo por forma de cobro / diario"), "", None, level=0, markup="rx_arc"
        )

        total_cash = 0.0
        total_ops = 0
        for journal in bank_cash_journals.sorted(lambda j: (j.company_id.name, j.name)):
            posted = daily._get_posted_moves_by_date(
                journal, company_ids, date_from, date_to, date_type
            )
            registered = posted.filtered(
                lambda m, j=journal: daily._is_move_bank_liquidity_registered(m, j)
            )
            subtotal = 0.0
            for move in registered:
                bal = daily._get_move_liquidity_balance(move, journal)
                subtotal += self._amount_to_report_currency(
                    bal,
                    journal.company_id,
                    options,
                    move.date,
                )
            n = len(registered)
            if not n:
                continue
            total_ops += n
            total_cash += subtotal
            add_row(
                journal.display_name,
                _("%(n)s operaciones", n=n),
                subtotal,
                level=1,
            )

        add_row(
            _("Total cobros registrados (diarios seleccionados)"),
            _("%(n)s operaciones", n=total_ops),
            total_cash,
            level=1,
            line_class="total",
        )

        refund_domain = self._invoice_domain_base(report, options, ("out_refund",))
        cancel_domain = [
            ("move_type", "in", tuple(self._cancel_move_types_customer())),
            ("state", "=", "cancel"),
            ("date", ">=", date_from),
            ("date", "<=", date_to),
            ("company_id", "in", company_ids),
        ]
        journal_domain = report._get_options_journals_domain(options)
        if journal_domain:
            cancel_domain += journal_domain

        invoices = self._search_sales_invoices_and_receipts(report, options)
        debit_notes = self._search_customer_debit_notes(report, options)
        refunds = self.env["account.move"].search(refund_domain, order="id asc")
        cancelled = self.env["account.move"].search(cancel_domain)

        sale_agg = self._aggregate_tax_maps(invoices, options=options)
        debit_agg = self._aggregate_tax_maps(debit_notes, options=options)
        refund_agg = self._aggregate_tax_maps(refunds, options=options)

        add_row(_("Ventas del período"), "", None, level=0, markup="rx_vs")
        add_row(
            _("Exento / exonerado"),
            "",
            sale_agg["total_exempt"],
            level=1,
        )
        company = main_company
        TaxGroup = self.env["account.tax.group"]
        tax_config = TaxGroup._l10n_ve_build_tax_config(company)
        if "general" in tax_config:
            percent = TaxGroup._l10n_ve_get_tax_rate_for_type(
                company, "general", "sale"
            )
            add_row(
                _("Base imponible — alícuota general (%(p)s%%)", p=percent),
                "",
                sale_agg["base_general"],
                level=1,
            )
            add_row(
                _("IVA — general"),
                "",
                sale_agg["amount_general"],
                level=1,
            )
        else:
            add_row(
                _("Base imponible — alícuota general"),
                "",
                sale_agg["base_general"],
                level=1,
            )
            add_row(_("IVA — general"), "", sale_agg["amount_general"], level=1)

        if "reduced" in tax_config:
            percent = TaxGroup._l10n_ve_get_tax_rate_for_type(
                company, "reduced", "sale"
            )
            add_row(
                _("Base imponible — alícuota reducida (%(p)s%%)", p=percent),
                "",
                sale_agg["base_reduced"],
                level=1,
            )
            add_row(
                _("IVA — reducida"),
                "",
                sale_agg["amount_reduced"],
                level=1,
            )
        else:
            add_row(
                _("Base imponible — reducida"),
                "",
                sale_agg["base_reduced"],
                level=1,
            )
            add_row(_("IVA — reducida"), "", sale_agg["amount_reduced"], level=1)

        if "extend" in tax_config:
            percent = TaxGroup._l10n_ve_get_tax_rate_for_type(
                company, "extend", "sale"
            )
            add_row(
                _("Base imponible — alícuota adicional (%(p)s%%)", p=percent),
                "",
                sale_agg["base_extend"],
                level=1,
            )
            add_row(
                _("IVA — adicional"),
                "",
                sale_agg["amount_extend"],
                level=1,
            )
        else:
            add_row(
                _("Base imponible — adicional"),
                "",
                sale_agg["base_extend"],
                level=1,
            )
            add_row(_("IVA — adicional"), "", sale_agg["amount_extend"], level=1)

        ttl_base_ventas = (
            sale_agg["total_exempt"]
            + sale_agg["base_general"]
            + sale_agg["base_reduced"]
            + sale_agg["base_extend"]
        )
        ttl_iva_ventas = (
            sale_agg["amount_general"]
            + sale_agg["amount_reduced"]
            + sale_agg["amount_extend"]
        )
        add_row(
            _("Total bases (ventas)"), "", ttl_base_ventas, level=1, line_class="total"
        )
        add_row(
            _("Total IVA (ventas)"), "", ttl_iva_ventas, level=1, line_class="total"
        )

        add_row(_("Notas de débito"), "", None, level=0, markup="rx_nd")
        add_row(
            _("Exento / exonerado (ND)"),
            "",
            debit_agg["total_exempt"],
            level=1,
        )
        if "general" in tax_config:
            percent = TaxGroup._l10n_ve_get_tax_rate_for_type(
                company, "general", "sale"
            )
            add_row(
                _("Base imponible — alícuota general (%(p)s%%) (ND)", p=percent),
                "",
                debit_agg["base_general"],
                level=1,
            )
            add_row(
                _("IVA — general (ND)"),
                "",
                debit_agg["amount_general"],
                level=1,
            )
        else:
            add_row(
                _("Base imponible — alícuota general (ND)"),
                "",
                debit_agg["base_general"],
                level=1,
            )
            add_row(_("IVA — general (ND)"), "", debit_agg["amount_general"], level=1)

        if "reduced" in tax_config:
            percent = TaxGroup._l10n_ve_get_tax_rate_for_type(
                company, "reduced", "sale"
            )
            add_row(
                _("Base imponible — alícuota reducida (%(p)s%%) (ND)", p=percent),
                "",
                debit_agg["base_reduced"],
                level=1,
            )
            add_row(
                _("IVA — reducida (ND)"),
                "",
                debit_agg["amount_reduced"],
                level=1,
            )
        else:
            add_row(
                _("Base imponible — reducida (ND)"),
                "",
                debit_agg["base_reduced"],
                level=1,
            )
            add_row(_("IVA — reducida (ND)"), "", debit_agg["amount_reduced"], level=1)

        if "extend" in tax_config:
            percent = TaxGroup._l10n_ve_get_tax_rate_for_type(
                company, "extend", "sale"
            )
            add_row(
                _("Base imponible — alícuota adicional (%(p)s%%) (ND)", p=percent),
                "",
                debit_agg["base_extend"],
                level=1,
            )
            add_row(
                _("IVA — adicional (ND)"),
                "",
                debit_agg["amount_extend"],
                level=1,
            )
        else:
            add_row(
                _("Base imponible — adicional (ND)"),
                "",
                debit_agg["base_extend"],
                level=1,
            )
            add_row(_("IVA — adicional (ND)"), "", debit_agg["amount_extend"], level=1)

        ttl_base_nd = (
            debit_agg["total_exempt"]
            + debit_agg["base_general"]
            + debit_agg["base_reduced"]
            + debit_agg["base_extend"]
        )
        ttl_iva_nd = (
            debit_agg["amount_general"]
            + debit_agg["amount_reduced"]
            + debit_agg["amount_extend"]
        )
        add_row(_("Total bases (ND)"), "", ttl_base_nd, level=1, line_class="total")
        add_row(_("Total IVA (ND)"), "", ttl_iva_nd, level=1, line_class="total")

        add_row(_("Notas de crédito / devoluciones"), "", None, level=0, markup="rx_nc")
        add_row(_("Exento (NC)"), "", abs(refund_agg["total_exempt"]), level=1)
        add_row(
            _("Base imponible — general (NC)"),
            "",
            abs(refund_agg["base_general"]),
            level=1,
        )
        add_row(_("IVA — general (NC)"), "", abs(refund_agg["amount_general"]), level=1)
        add_row(
            _("Base imponible — reducida (NC)"),
            "",
            abs(refund_agg["base_reduced"]),
            level=1,
        )
        add_row(
            _("IVA — reducida (NC)"), "", abs(refund_agg["amount_reduced"]), level=1
        )
        add_row(
            _("Base imponible — adicional (NC)"),
            "",
            abs(refund_agg["base_extend"]),
            level=1,
        )
        add_row(
            _("IVA — adicional (NC)"), "", abs(refund_agg["amount_extend"]), level=1
        )
        ttl_base_nc = (
            abs(refund_agg["total_exempt"])
            + abs(refund_agg["base_general"])
            + abs(refund_agg["base_reduced"])
            + abs(refund_agg["base_extend"])
        )
        ttl_iva_nc = (
            abs(refund_agg["amount_general"])
            + abs(refund_agg["amount_reduced"])
            + abs(refund_agg["amount_extend"])
        )
        add_row(_("Total bases (NC)"), "", ttl_base_nc, level=1, line_class="total")
        add_row(_("Total IVA (NC)"), "", ttl_iva_nc, level=1, line_class="total")

        disc = self._discount_total_report_currency(invoices | debit_notes, options)
        add_row(_("Descuentos (estimado en líneas de factura)"), "", disc, level=0)

        add_row(_("Anulaciones (documentos cancelados en el período)"), "", None, level=0)
        add_row(
            _("Documentos cancelados"),
            _("%(n)s documentos", n=len(cancelled)),
            self._cancelled_total_report_currency(cancelled, options),
            level=1,
        )

        add_row(_("Documentos emitidos (referencia Odoo)"), "", None, level=0)
        if invoices:
            last_inv = max(invoices, key=lambda m: (m.invoice_date or m.date, m.id))
            add_row(
                _("Última factura / recibo"),
                last_inv.name or "",
                None,
                level=1,
            )
        add_row(
            _("Cantidad facturas y recibos"),
            "",
            len(invoices),
            level=1,
        )
        if debit_notes:
            last_nd = max(
                debit_notes, key=lambda m: (m.invoice_date or m.date, m.id)
            )
            add_row(
                _("Última nota de débito"),
                last_nd.name or "",
                None,
                level=1,
            )
        add_row(
            _("Cantidad notas de débito"),
            "",
            len(debit_notes),
            level=1,
        )
        if refunds:
            last_nc = max(refunds, key=lambda m: (m.invoice_date or m.date, m.id))
            add_row(
                _("Última nota de crédito"),
                last_nc.name or "",
                None,
                level=1,
            )
        add_row(
            _("Cantidad notas de crédito"),
            "",
            len(refunds),
            level=1,
        )

        if hasattr(self.env["account.move"], "l10n_ve_control_number"):
            fiscal_docs = invoices | debit_notes
            with_control = fiscal_docs.filtered(
                lambda m: (m.l10n_ve_control_number or "").strip()
                and m.l10n_ve_control_number != "/"
            )
            without_control = fiscal_docs - with_control
            add_row(
                _("Documentos de venta con n° de control"),
                "",
                len(with_control),
                level=1,
            )
            add_row(
                _("Documentos sin n° de control (no fiscal)"),
                "",
                len(without_control),
                level=1,
            )

        return lines
