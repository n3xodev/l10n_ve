from odoo import Command
from odoo.tests import HttpCase, tagged

from .common import TestL10nVeIgtfCommon

WAIT_FOR_SELECTOR_JS = """
const waitFor = async (selector, timeout = 60000) => {
    const start = Date.now();
    while (Date.now() - start < timeout) {
        const el = document.querySelector(selector);
        if (el) {
            return el;
        }
        await new Promise((resolve) => setTimeout(resolve, 100));
    }
    throw new Error("Timeout waiting for selector: " + selector);
};

const run = async (body) => {
    try {
        await body();
        console.log("test successful");
    } catch (error) {
        console.error(error.message);
    }
};
"""


@tagged("post_install", "-at_install")
class TestIgtfPaymentWidgetUi(TestL10nVeIgtfCommon, HttpCase):
    def setUp(self):
        super().setUp()
        # The test company is not the default company of the admin user.
        admin = self.env.ref("base.user_admin")
        admin.write(
            {
                "company_ids": [Command.link(self.company.id)],
                "company_id": self.company.id,
            }
        )

    def _invoice_form_url(self, invoice):
        return f"/odoo/account.move/{invoice.id}"

    def test_outstanding_credits_widget_renders_without_js_error(self):
        """The IGTF xpath must not break the outstanding credits section."""
        payment = self.env["account.payment"].create(
            {
                "payment_type": "inbound",
                "partner_type": "customer",
                "partner_id": self.partner.id,
                "amount": 50.0,
                "currency_id": self.ves.id,
                "journal_id": self.bank_journal.id,
                "date": self.test_date,
            }
        )
        payment.action_post()
        invoice = self._create_customer_invoice(amount=100.0, currency=self.ves)

        self.browser_js(
            self._invoice_form_url(invoice),
            WAIT_FOR_SELECTOR_JS
            + """
            run(async () => {
            await waitFor(".o_form_view [name='invoice_outstanding_credits_debits_widget'] #outstanding");
            await waitFor(".o_form_view .outstanding_credit_assign");
            });
            """,
            ready="odoo.isReady",
            login="admin",
            timeout=120,
        )

    def test_igtf_row_renders_under_payment_line(self):
        """The IGTF row must still render below each reconciled payment line."""
        invoice = self._create_customer_invoice(amount=100.0, currency=self.ves)
        self._register_invoice_payment(
            invoice,
            amount=self._usd_amount_for_ves(100.0),
            currency=self.usd,
            apply_igtf=True,
        )

        self.browser_js(
            self._invoice_form_url(invoice),
            WAIT_FOR_SELECTOR_JS
            + """
            run(async () => {
            await waitFor(".o_form_view [name='invoice_payments_widget'] .js_payment_info");
            const text = document.querySelector(
                ".o_form_view [name='invoice_payments_widget']"
            ).textContent;
            if (!text.includes("IGTF - ")) {
                throw new Error("IGTF row not rendered: " + text);
            }
            });
            """,
            ready="odoo.isReady",
            login="admin",
            timeout=120,
        )
