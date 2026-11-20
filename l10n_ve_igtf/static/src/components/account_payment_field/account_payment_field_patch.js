/** @odoo-module **/

import {Component, t, useProps} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {localization} from "@web/core/l10n/localization";
import {patch} from "@web/core/utils/patch";
import {usePopover} from "@web/core/popover/popover_hook";
import {AccountPaymentField} from "@account/components/account_payment_field/account_payment_field";

// Core AccountPaymentPopOver is not exported and its useProps schema only
// exposes the keys it declares, so the IGTF keys need their own popover.
class L10nVeIgtfAccountPaymentPopOver extends Component {
    static template = "l10n_ve_igtf.AccountPaymentPopOver";

    props = useProps({
        _onOpenMove: t.function(),
        _onRemoveMoveReconcile: t.function(),
        amount_company_currency: t.string(),
        amount_foreign_currency: t.or([t.string(), t.literal(null)]).optional(),
        close: t.function(),
        company_name: t.or([t.string(), t.literal(false)]),
        date: t.string(),
        journal_name: t.string(),
        move_id: t.or([t.number(), t.literal(false)]),
        partial_id: t.or([t.number(), t.literal(false)]),
        payment_method_name: t.or([t.string(), t.literal(false)]).optional(),
        ref: t.string(),
        title: t.string(),
        l10n_ve_igtf_amount_formatted: t.or([t.string(), t.literal(false)]).optional(),
        l10n_ve_igtf_amount_company_currency_formatted: t
            .or([t.string(), t.literal(false)])
            .optional(),
        l10n_ve_net_amount_formatted: t.or([t.string(), t.literal(false)]).optional(),
    });
}

patch(AccountPaymentField.prototype, {
    setup() {
        super.setup();
        const position = localization.direction === "rtl" ? "bottom" : "left";
        this.popover = usePopover(L10nVeIgtfAccountPaymentPopOver, {position});
    },

    onInfoClick(ev, line) {
        this.popover.open(ev.currentTarget, {
            title: _t("Journal Entry Info"),
            ...line,
            l10n_ve_igtf_amount_formatted: line.l10n_ve_igtf_amount_formatted,
            l10n_ve_igtf_amount_company_currency_formatted:
                line.l10n_ve_igtf_amount_company_currency_formatted,
            l10n_ve_net_amount_formatted: line.l10n_ve_net_amount_formatted,
            _onRemoveMoveReconcile: this.removeMoveReconcile.bind(this),
            _onOpenMove: this.openMove.bind(this),
        });
    },

    async removeMoveReconcile(moveId, partialId) {
        const action = await this.orm.call(
            this.props.record.resModel,
            "l10n_ve_igtf_get_unreconcile_action",
            [moveId, partialId],
            {}
        );
        if (action) {
            this.popover.close();
            let reloaded = false;
            await this.action.doAction(action, {
                onClose: async () => {
                    if (!reloaded) {
                        reloaded = true;
                        await this.props.record.model.root.load();
                    }
                },
            });
            if (!reloaded) {
                await new Promise((resolve) => setTimeout(resolve, 100));
                await this.props.record.model.root.load();
            }
            return;
        }
        this.popover.close();
        await this.orm.call(
            this.props.record.resModel,
            "js_remove_outstanding_partial",
            [moveId, partialId],
            {}
        );
        await this.props.record.model.root.load();
    },
});
