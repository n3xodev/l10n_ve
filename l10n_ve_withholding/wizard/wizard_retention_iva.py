import re
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class TxtWizard(models.TransientModel):
    _name = "wizard.retention.iva"
    _description = "File IVA taxes with the SENIAT"

    date_start = fields.Date(
        default=lambda self: fields.Date.context_today(self).replace(day=1)
    )
    date_end = fields.Date(
        default=lambda self: fields.Date.context_today(self).replace(day=1)
        + relativedelta(months=1, days=-1)
    )

    @api.model
    def _get_retention_domain(self, date_start, date_end, company_id):
        return [
            ("date_accounting", ">=", date_start),
            ("date_accounting", "<=", date_end),
            ("state", "=", "emitted"),
            ("type_retention", "=", "iva"),
            ("type", "in", ("in_invoice", "in_refund", "in_debit")),
            ("company_id", "=", company_id),
        ]

    @api.model
    def _format_seniat_rif(self, partner):
        if not partner:
            return ""
        prefix_vat = (partner.prefix_vat or "").strip().upper()
        partner_vat = (partner.vat or "").strip().upper()
        raw_rif = partner_vat
        if prefix_vat and not partner_vat.startswith(prefix_vat):
            raw_rif = f"{prefix_vat}{partner_vat}"
        normalized = re.sub(r"[^A-Z0-9]", "", raw_rif)
        if not normalized:
            return ""
        # Strip ISO country prefix (e.g. "VEJ123456789" -> "J123456789")
        if len(normalized) > 2 and normalized.startswith("VE") and normalized[2] in "VEJPGC":
            normalized = normalized[2:]
        first_alpha = next((char for char in normalized if char.isalpha()), "")
        digits = "".join(char for char in normalized if char.isdigit())
        if first_alpha and digits:
            return f"{first_alpha}{digits.zfill(9)}"
        return f"{first_alpha}{digits}" if first_alpha else digits

    def generate_txt(self):
        company_id = self.env.company.id
        if not (self.date_start and self.date_end):
            raise UserError(_("You must enter a start and end date"))
        if self.date_start > self.date_end:
            raise UserError(_("The start date cannot be greater than the end date."))
        retention_count = self.env["account.retention"].search_count(
            self._get_retention_domain(self.date_start, self.date_end, company_id)
        )
        if retention_count == 0:
            raise UserError(_("No retentions found for the selected period"))

        url = f"/web/binary/download_retention_iva_txt?date_start={self.date_start}&date_end={self.date_end}&company_id={company_id!s}"  # noqa: E501
        return {"type": "ir.actions.act_url", "url": url, "target": "self"}

    @api.model
    def _get_move_exempt_amount(self, move):
        """Return exempt amount in company currency (VES) for a vendor move."""
        exempt_lines = move.invoice_line_ids.filtered(
            lambda inv_line: inv_line.display_type == "product"
            and (
                not inv_line.tax_ids
                or all(tax.amount == 0 for tax in inv_line.tax_ids)
            )
        )
        return abs(sum(exempt_lines.mapped("balance")))

    def _retention_iva(self, retentions):
        document_types = {
            "in_invoice": "01",
            "in_debit": "02",
            "in_refund": "03",
        }

        sorted_lines = retentions.mapped("retention_line_ids").sorted(
            key=lambda line: (
                line.retention_id.date_accounting
                or line.retention_id.date
                or date.min,
                line.move_id.invoice_date or line.move_id.date or date.min,
                line.retention_id.id,
                line.id,
            )
        )

        seen_move_ids = set()
        data = []
        for line in sorted_lines:
            move = line.move_id
            retention = line.retention_id
            period_date = retention.date_accounting or retention.date
            invoice_date = move.invoice_date or move.date

            partner = (
                move._l10n_ve_withholding_partner()
                if hasattr(move, "_l10n_ve_withholding_partner")
                else (retention.partner_id or move.partner_id)
            )

            line_data = {}
            line_data["RIF del agente de retención"] = self._format_seniat_rif(
                retention.company_id.partner_id
            )
            line_data["Período impositivo"] = (
                period_date.strftime("%Y%m") if period_date else ""
            )
            line_data["Fecha de factura"] = (
                invoice_date.strftime("%Y-%m-%d") if invoice_date else ""
            )
            line_data["Tipo de operación"] = "C"

            if move.debit_origin_id:
                line_data["Tipo de documento"] = document_types["in_debit"]
                orig = move.debit_origin_id
                line_data["Número del documento afectado"] = (
                    orig.ref or orig.name or "0"
                )
            else:
                line_data["Tipo de documento"] = document_types.get(
                    move.move_type, "01"
                )
                rev = move.reversed_entry_id
                line_data["Número del documento afectado"] = (
                    (rev.ref or rev.name or "0") if rev else "0"
                )

            line_data["RIF de proveedor"] = self._format_seniat_rif(partner)
            line_data["Número de documento"] = move.ref or move.name or ""
            line_data["Número de control"] = (
                move.l10n_ve_control_number or ""
            ).strip()
            line_data["Número de comprobante de retención"] = (
                retention.number or "0"
            ).strip()
            line_data["Alícuota"] = line.aliquot

            if move.id not in seen_move_ids:
                exempt_amount = self._get_move_exempt_amount(move)
                seen_move_ids.add(move.id)
            else:
                exempt_amount = 0.0

            line_data["Monto total del documento"] = (
                line.invoice_amount + line.iva_amount + exempt_amount
            )
            line_data["Base imponible"] = line.invoice_amount
            line_data["Monto del Iva Retenido"] = line.retention_amount
            line_data["Monto exento del IVA"] = exempt_amount
            line_data["Número de Expediente"] = "0"
            data.append(line_data)
        return data

    @api.model
    def _build_txt_content(self, retentions):
        data = self._retention_iva(retentions)
        rows = []
        for row in data:
            columns = [
                str(row.get("RIF del agente de retención") or ""),
                str(row.get("Período impositivo") or ""),
                str(row.get("Fecha de factura") or ""),
                str(row.get("Tipo de operación") or ""),
                str(row.get("Tipo de documento") or ""),
                str(row.get("RIF de proveedor") or ""),
                str(row.get("Número de documento") or ""),
                str(row.get("Número de control") or ""),
                "{:.2f}".format(row.get("Monto total del documento") or 0.0),
                "{:.2f}".format(row.get("Base imponible") or 0.0),
                "{:.2f}".format(row.get("Monto del Iva Retenido") or 0.0),
                str(row.get("Número del documento afectado") or "0"),
                str(row.get("Número de comprobante de retención") or "0"),
                "{:.2f}".format(row.get("Monto exento del IVA") or 0.0),
                "{:.2f}".format(row.get("Alícuota") or 0.0),
                str(row.get("Número de Expediente") or "0"),
            ]
            rows.append("\t".join(columns))
        return "\r\n".join(rows) + ("\r\n" if rows else "")
