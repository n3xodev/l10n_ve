/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";

function isVenezuelaCompany(pos) {
    return (
        pos.company?.country_id?.code === "VE" ||
        pos.company?.account_fiscal_country_id?.code === "VE"
    );
}

patch(PosStore.prototype, {
    getPotentialFreeProductRewards() {
        const order = this.getOrder();
        if (!order?.uiState) {
            return [];
        }
        return super.getPotentialFreeProductRewards(...arguments);
    },

    /**
     * Hook: id of the partner whose eWallet cards are fetched for `partnerId`.
     * The default is the partner itself; other modules may map it elsewhere.
     */
    _l10nVeEwalletPartnerId(partnerId) {
        return partnerId;
    },

    async _l10nVeRefreshPartnerEwalletCards(partnerId) {
        partnerId = this._l10nVeEwalletPartnerId(partnerId);
        if (!isVenezuelaCompany(this) || !partnerId) {
            return;
        }
        const ewalletPrograms = (this.models["loyalty.program"]?.getAll?.() || []).filter(
            (program) => program.program_type === "ewallet"
        );
        if (!ewalletPrograms.length || typeof this.fetchCoupons !== "function") {
            return;
        }
        const programIds = ewalletPrograms.map((program) => program.id);
        const fetched = await this.fetchCoupons(
            [
                ["partner_id", "=", partnerId],
                ["program_id", "in", programIds],
            ],
            programIds.length || 1
        );
        for (const remote of fetched || []) {
            const local = this.models["loyalty.card"].get(remote.id);
            if (local) {
                local.update({ points: remote.points });
            }
        }
        return fetched;
    },

    async fetchLoyaltyCard(programId, partnerId) {
        partnerId = this._l10nVeEwalletPartnerId(partnerId);
        const program = this.models["loyalty.program"]?.get?.(programId);
        if (
            isVenezuelaCompany(this) &&
            program?.program_type === "ewallet" &&
            partnerId &&
            typeof this.fetchCoupons === "function"
        ) {
            const fetchedCoupons = await this.fetchCoupons(
                [
                    ["partner_id", "=", partnerId],
                    ["program_id", "=", programId],
                ],
                1
            );
            if (fetchedCoupons?.length) {
                const remote = fetchedCoupons[0];
                const local = this.models["loyalty.card"].get(remote.id);
                if (local) {
                    local.update({ points: remote.points });
                    return local;
                }
                return remote;
            }
        }
        return await super.fetchLoyaltyCard(...arguments);
    },

    async selectPartner(partner) {
        const res = await super.selectPartner(...arguments);
        const selected = this.getOrder()?.getPartner?.() || partner;
        if (selected?.id) {
            await this._l10nVeRefreshPartnerEwalletCards(selected.id);
            if (typeof this.updateRewards === "function") {
                this.updateRewards();
            }
        }
        return res;
    },
});

