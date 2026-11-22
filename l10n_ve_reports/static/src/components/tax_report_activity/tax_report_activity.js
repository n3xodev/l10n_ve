/** @odoo-module */
import {patch} from "@web/core/utils/patch";
import {useService} from "@web/core/utils/hooks";
import {ActivityListPopoverItem} from "@mail/core/web/activity_list_popover_item";

patch(ActivityListPopoverItem.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
    },

    get isTaxReportActivity() {
        return this.activity().activity_category === "tax_report";
    },

    async onClickOpenTaxActivity() {
        const action = await this.orm.call(
            "mail.activity",
            "action_open_tax_activity",
            [this.activity().id],
            {}
        );
        this.onActivityChanged?.();
        this.action.doAction(action);
    },
});
