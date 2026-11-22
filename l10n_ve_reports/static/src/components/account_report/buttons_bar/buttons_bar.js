/** @odoo-module */

import { Component, proxy, useProps } from "@odoo/owl";

export class AccountReportButtonsBar extends Component {
    static template = "l10n_ve_reports.AccountReportButtonsBar";
    props = useProps({});

    setup() {
        this.controller = proxy(this.env.controller);
    }

    //------------------------------------------------------------------------------------------------------------------
    // Buttons
    //------------------------------------------------------------------------------------------------------------------
    get barButtons() {
        const buttons = [];

        for (const button of this.controller.buttons) {
            if (button.always_show) {
                buttons.push(button);
            }
        }

        return buttons;
    }
}
