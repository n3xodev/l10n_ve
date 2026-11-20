/** @odoo-module */

import { Component, onWillStart, proxy, usePlugin } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ActionPlugin } from "@web/webclient/actions/action_plugin";

export class EdiUnsentDashboard extends Component {
    static template = "l10n_ve_edi.EdiUnsentDashboard";

    setup() {
        this.orm = useService("orm");
        this.actionService = usePlugin(ActionPlugin);
        this.state = proxy({
            visible: false,
            title: "",
            items: [],
        });

        onWillStart(async () => {
            await this.loadDashboard();
        });
    }

    async loadDashboard() {
        const data = await this.orm.call(
            "account.journal",
            "get_l10n_ve_edi_unsent_dashboard",
            []
        );
        this.state.visible = data.visible;
        this.state.title = data.title || "";
        this.state.items = data.items || [];
    }

    async openItem(itemKey) {
        const action = await this.orm.call(
            "account.journal",
            "action_l10n_ve_edi_unsent_dashboard_open",
            [itemKey]
        );
        return this.actionService.doAction(action);
    }
}
