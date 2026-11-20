import { patch } from "@web/core/utils/patch";
import { AccountSidebar } from "@account/interactions/account_sidebar";

patch(AccountSidebar.prototype, {
    _l10nVeEdiTfhkaHasHtmlDoc() {
        if (!this.invoiceHTMLEl) {
            return false;
        }
        try {
            const doc = this.invoiceHTMLEl.contentDocument;
            return Boolean(doc && doc.querySelector("div#wrapwrap"));
        } catch {
            return false;
        }
    },

    onIframeLoad() {
        if (!this._l10nVeEdiTfhkaHasHtmlDoc()) {
            this.updateIframeSize();
            return;
        }
        if (!this.invoiceHTMLEl.contentDocument?.querySelector("main")) {
            this.updateIframeSize();
            return;
        }
        return super.onIframeLoad(...arguments);
    },

    updateIframeSize() {
        if (!this.invoiceHTMLEl) {
            return;
        }
        if (!this._l10nVeEdiTfhkaHasHtmlDoc()) {
            const h = Math.max(720, Math.min(window.innerHeight - 120, 1400));
            this.invoiceHTMLEl.style.transform = "";
            this.invoiceHTMLEl.width = "100%";
            this.invoiceHTMLEl.height = h;
            if (this.invoiceHTMLEl.parentElement) {
                this.invoiceHTMLEl.parentElement.style.height = `${h}px`;
            }
            return;
        }
        return super.updateIframeSize(...arguments);
    },
});
