/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import OrderPaymentValidation from "@point_of_sale/app/utils/order_payment_validation";
import { patch } from "@web/core/utils/patch";
import {
    l10nVeFiscalSerialPosExecutePrint,
    l10nVeFiscalSerialPosGetNextPlaceholders,
    l10nVeFiscalSerialPosIsFiscalMachine,
    l10nVeFiscalSerialPosIsOffline,
} from "../../fiscal_serial_pos_print";

function isVenezuelaCompany(pos) {
    return (
        pos.company?.country_id?.code === "VE" ||
        pos.company?.account_fiscal_country_id?.code === "VE"
    );
}

patch(PaymentScreen.prototype, {
    _l10nVeApplyLocalFiscalPlaceholders() {
        if (!l10nVeFiscalSerialPosIsFiscalMachine(this.pos)) {
            return;
        }
        const placeholders = l10nVeFiscalSerialPosGetNextPlaceholders(this.pos);
        if (placeholders.invoice_number) {
            this.l10nVeEmission.next_fiscal_invoice_number = placeholders.invoice_number;
        }
        if (placeholders.serial) {
            this.l10nVeEmission.next_fiscal_serial = placeholders.serial;
        }
        if (placeholders.report_z) {
            this.l10nVeEmission.next_fiscal_report_z = placeholders.report_z;
        }
    },

    async l10nVeRefreshEmissionPreview() {
        if (l10nVeFiscalSerialPosIsOffline(this.pos)) {
            const fallback =
                typeof this._l10nVeLocalEmissionPreviewFallback === "function"
                    ? this._l10nVeLocalEmissionPreviewFallback()
                    : false;
            if (fallback && typeof this._l10nVeApplyEmissionPreview === "function") {
                this._l10nVeApplyEmissionPreview(fallback);
            }
            this._l10nVeApplyLocalFiscalPlaceholders();
            return;
        }
        await super.l10nVeRefreshEmissionPreview(...arguments);
        this._l10nVeApplyLocalFiscalPlaceholders();
    },
});

// Odoo 20 runs every order validation (payment screen, quick payment buttons,
// electronic auto-validation) through `OrderPaymentValidation`, so the fiscal
// printing hook lives there.
//
// Core `validateOrder` ignores the outcome of `shouldHideValidationBehindFeedbackScreen`
// and removes the pending/zero payment lines before calling it, so a failure there
// cannot abort anything. The print therefore runs from `isOrderValid`, the only
// step whose `false` really aborts: `validateOrder` returns false (so do
// `pos.validateOrder` / `autoValidateOrder`), the payment lines are untouched
// and the order stays on its screen so the cashier can retry.
//
// The print result is remembered per order (`printedUuids`) and shared by every
// path, because the fiscal number can be empty after a successful print and a
// retry after a later validation error must not print a second fiscal document.
//
// Known limitations:
// - `afterOrderValidation` is a fallback for paths that skip `isOrderValid`
//   (ConnectionLostError recovery, TipScreen finalization). It runs after the
//   order was finalized, so a failure there cannot abort the validation: the
//   cashier is notified and the order continues.
// - With `set_tip_after_payment` the tip is added after the validation, so the
//   fiscal document is printed without the tip amount.
const printedOrders = new WeakMap();

function printedUuids(pos) {
    if (!printedOrders.has(pos)) {
        printedOrders.set(pos, new Set());
    }
    return printedOrders.get(pos);
}

patch(OrderPaymentValidation.prototype, {
    _l10nVeFiscalSerialNeedsPrint() {
        if (!isVenezuelaCompany(this.pos)) {
            return false;
        }
        if (!l10nVeFiscalSerialPosIsFiscalMachine(this.pos)) {
            return false;
        }
        const order = this.order;
        if (!order?.isToInvoice() || printedUuids(this.pos).has(order.uuid)) {
            return false;
        }
        return !(
            order.l10n_ve_pos_fiscal_invoice_number ||
            order.raw?.l10n_ve_pos_fiscal_invoice_number
        );
    },
    async _l10nVeFiscalSerialPrint() {
        const ok = await l10nVeFiscalSerialPosExecutePrint({
            pos: this.pos,
            env: this.pos.env,
            orderId: this.order.id,
            order: this.order,
        });
        if (ok) {
            printedUuids(this.pos).add(this.order.uuid);
        }
        return ok;
    },
    async isOrderValid() {
        if (!(await super.isOrderValid(...arguments))) {
            return false;
        }
        if (this._l10nVeFiscalSerialNeedsPrint()) {
            return this._l10nVeFiscalSerialPrint();
        }
        return true;
    },
    async afterOrderValidation() {
        if (this._l10nVeFiscalSerialNeedsPrint()) {
            // The order is already finalized: nothing to abort, the failure is
            // notified by the print helper.
            await this._l10nVeFiscalSerialPrint();
        }
        return super.afterOrderValidation(...arguments);
    },
});
