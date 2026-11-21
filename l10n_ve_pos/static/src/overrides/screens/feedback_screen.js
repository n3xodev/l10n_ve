import { FeedbackScreen } from "@point_of_sale/app/screens/feedback_screen/feedback_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";

function isVenezuelaCompany(pos) {
    return (
        pos.company?.country_id?.code === "VE" ||
        pos.company?.account_fiscal_country_id?.code === "VE"
    );
}

// Odoo 20 replaced the ReceiptScreen (receipt preview + print/email options) with
// the FeedbackScreen. Venezuelan documents are printed from the invoice (or the
// fiscal machine), so for VE companies the screen shows the invoice/fiscal
// numbers instead of the POS receipt actions.
patch(FeedbackScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.invoiceService = useService("account_move");
    },
    get isVenezuelaPos() {
        return isVenezuelaCompany(this.pos);
    },
    get canPrintReceipt() {
        return this.isVenezuelaPos ? false : super.canPrintReceipt;
    },
    get canSendReceipt() {
        return this.isVenezuelaPos ? false : this.pos.canSendReceipt;
    },
    // The invoice numbers must stay on screen until the cashier continues.
    get isAutoSkip() {
        return this.isVenezuelaPos ? false : super.isAutoSkip;
    },
    get l10nVeShowReceiptInvoiceDetails() {
        return (
            this.isVenezuelaPos &&
            !this.loading() &&
            Boolean(this.currentOrder.raw?.account_move)
        );
    },
    get l10nVeJournalEmissionMedium() {
        const orderJournal = this.currentOrder?.invoice_journal_id;
        return (
            orderJournal?.l10n_ve_emission_medium ||
            this.pos.config?.journal_id?.l10n_ve_emission_medium ||
            ""
        );
    },
    get l10nVeLabelAccountingInvoiceNumber() {
        return _t("Accounting invoice number");
    },
    get l10nVeLabelFiscalInvoiceNo() {
        return _t("Fiscal invoice number");
    },
    get l10nVeLabelFiscalSerial() {
        return _t("Fiscal machine serial");
    },
    get l10nVeLabelFiscalZ() {
        return _t("Z report number");
    },
    get l10nVeLabelControlNumber() {
        return _t("Control number");
    },
    get l10nVeShowFormaLibreDownload() {
        return (
            this.l10nVeJournalEmissionMedium === "free" &&
            Boolean(this.currentOrder.raw?.account_move)
        );
    },
    get l10nVeDownloadFormaLibreLabel() {
        return _t("Download free-form PDF");
    },
    get l10nVeDash() {
        return "—";
    },
    async l10nVeDownloadFormaLibre() {
        const moveId = this.currentOrder.raw?.account_move;
        if (!moveId) {
            return;
        }
        try {
            await this.invoiceService.downloadPdf(moveId);
        } catch {
            this.notification.add(_t("Could not download the invoice."), { type: "danger" });
        }
    },
});
