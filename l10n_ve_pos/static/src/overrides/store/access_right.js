import { PosAccessRightPlugin } from "@point_of_sale/app/plugins/access_right_plugin";
import { patch } from "@web/core/utils/patch";

// Odoo 20 moved the "can create products" decision from `PosStore.allowProductCreation`
// to `PosAccessRightPlugin.hasProductCreationAccess`. Products are never created
// from the Point of Sale of a Venezuelan company.
patch(PosAccessRightPlugin.prototype, {
    get hasProductCreationAccess() {
        const company = this.data.models["res.company"].getFirst();
        if (
            company?.country_id?.code === "VE" ||
            company?.account_fiscal_country_id?.code === "VE"
        ) {
            return false;
        }
        return super.hasProductCreationAccess;
    },
});
