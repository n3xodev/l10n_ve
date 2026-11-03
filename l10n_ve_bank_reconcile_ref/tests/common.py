# Copyright 2026 andyengit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class RefReconcileCommon(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.partner_a
        cls.bank_journal = cls.company_data["default_journal_bank"]

    def _create_invoice(self, amount, reference, partner=None):
        invoice = self.init_invoice(
            "out_invoice",
            partner=partner or self.partner,
            invoice_date="2026-03-01",
            post=True,
            amounts=[amount],
        )
        invoice.write({"payment_reference": reference})
        return invoice

    def _create_payment(self, amount, reference, partner=None):
        payment = self.env["account.payment"].create(
            {
                "amount": amount,
                "payment_type": "inbound",
                "partner_type": "customer",
                "partner_id": (partner or self.partner).id,
                "payment_reference": reference,
                "memo": reference,
                "journal_id": self.bank_journal.id,
            }
        )
        payment.action_post()
        return payment

    def _create_st_line(self, amount, payment_ref, partner=None, **extra):
        """Create a statement line running the real auto reconcile flow."""
        vals = {
            "journal_id": self.bank_journal.id,
            "amount": amount,
            "date": "2026-03-10",
            "payment_ref": payment_ref,
            "partner_id": (partner or self.partner).id,
            **extra,
        }
        return (
            self.env["account.bank.statement.line"]
            .with_context(_test_account_reconcile_oca=True)
            .create(vals)
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
            lambda line: line.account_id.account_type == "asset_receivable"
        )
