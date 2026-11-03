# Copyright 2026 andyengit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class RefReconcileCommon(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.partner_a
        cls.bank_journal = cls.company_data["default_journal_bank"]

    def _create_invoice(self, amount, reference, partner=None, move_type="out_invoice"):
        invoice = self.init_invoice(
            move_type,
            partner=partner or self.partner,
            invoice_date="2026-03-01",
            post=False,
            amounts=[amount],
        )
        # A single receivable/payable line, whatever the default payment terms.
        invoice.invoice_payment_term_id = False
        invoice.action_post()
        invoice.write({"payment_reference": reference})
        return invoice

    def _create_payment(
        self, amount, reference, partner=None, payment_type="inbound", journal=None
    ):
        payment = self.env["account.payment"].create(
            {
                "amount": amount,
                "payment_type": payment_type,
                "partner_type": "customer" if payment_type == "inbound" else "supplier",
                "partner_id": (partner or self.partner).id,
                "payment_reference": reference,
                "memo": reference,
                "journal_id": (journal or self.bank_journal).id,
            }
        )
        payment.action_post()
        return payment

    def _st_line_vals(self, amount, payment_ref, partner=None, **extra):
        partner = self.partner if partner is None else partner
        return {
            "journal_id": self.bank_journal.id,
            "amount": amount,
            "date": "2026-03-10",
            "payment_ref": payment_ref,
            "partner_id": partner.id if partner else False,
            **extra,
        }

    def _create_st_line(self, amount, payment_ref, partner=None, **extra):
        """Create a statement line running the real auto reconcile flow."""
        return self._create_st_lines(
            [self._st_line_vals(amount, payment_ref, partner, **extra)]
        )

    def _create_st_lines(self, vals_list):
        return (
            self.env["account.bank.statement.line"]
            .with_context(_test_account_reconcile_oca=True)
            .create(vals_list)
        )

    def _counterpart_amls(self, st_line):
        """Journal items the line proposes or reconciled against."""
        ids = [
            line_id
            for line in st_line.reconcile_data_info["data"]
            if line["kind"] == "other"
            for line_id in line.get("counterpart_line_ids", [])
        ]
        return self.env["account.move.line"].browse(ids)

    def _payment_aml(self, payment):
        return payment.move_id.line_ids.filtered(
            lambda line: line.account_id.account_type
            not in ("asset_receivable", "liability_payable")
        )

    def _invoice_aml(self, invoice):
        return invoice.line_ids.filtered(
            lambda line: line.account_id.account_type
            in ("asset_receivable", "liability_payable")
        )
