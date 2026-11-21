import { PartnerList } from "@point_of_sale/app/screens/partner_list/partner_list";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(PartnerList.prototype, {
    onSearchInputKeydown(ev) {
        if (ev.key !== "Enter") {
            return;
        }
        ev.preventDefault();
        ev.stopPropagation();
        this.onEnter();
    },
    _l10nVeGetAllPartners() {
        // Core renders the preloaded and the server-loaded partners as two lists;
        // Enter acts on both, and Odoo 19's getPartners() requires the list.
        return this.getPartners([
            ...this.state.initialPartners,
            ...this.state.loadedPartners,
        ]);
    },
    async onEnter() {
        // The search input is debounced, so state.query may lag behind what the
        // user typed: read the live DOM value first (same as core's onEnter).
        const inputElement = this.searchInputRef?.();
        if (inputElement) {
            this.state.query = inputElement.value;
        }
        const query = (this.state.query || "").trim();
        if (!query) {
            return;
        }

        const localPartners = this._l10nVeGetAllPartners();
        if (localPartners.length === 1) {
            this.clickPartner(localPartners[0]);
            return;
        }

        if (localPartners.length === 0) {
            await this.searchPartner();
            const partnersAfterSearchMore = this._l10nVeGetAllPartners();

            if (partnersAfterSearchMore.length === 1) {
                this.clickPartner(partnersAfterSearchMore[0]);
                return;
            }

            if (partnersAfterSearchMore.length === 0) {
                this.pos.l10n_ve_partner_create_query = query;
                try {
                    await this.editPartner();
                } finally {
                    this.pos.l10n_ve_partner_create_query = null;
                }
                return;
            }
        }

        this.notification.add(
            _t('%s customer(s) found for "%s".', this._l10nVeGetAllPartners().length, query),
            3000
        );
    },
});
