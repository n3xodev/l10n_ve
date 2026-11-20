/** @odoo-module **/

import { Component, usePlugin, useProps, xml } from "@odoo/owl";
import { NotificationPlugin } from "@web/core/notifications/notification_plugin";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { l10nVeFiscalSerialExecuteReport } from "../fiscal_serial/fiscal_serial_report";

const ACTION_LABELS = {
    report_x: _t("Reporte X"),
    report_z: _t("Reporte Z"),
};

export class FiscalReportButton extends Component {
    props = useProps();
    static template = xml`
        <button t-att-class="this.buttonClass" type="button" t-on-click="this.onClick">
            <span t-out="this.label"/>
        </button>
    `;

    setup() {
        this.notification = usePlugin(NotificationPlugin);
    }

    get label() {
        return ACTION_LABELS[this.props.action] || _t("Reporte fiscal");
    }

    get buttonClass() {
        return `btn ${this.props.button_class || "btn-secondary"}`;
    }

    async onClick() {
        const action = this.props.action;
        if (!action) {
            this.notification.add(_t("Acción fiscal no configurada."), { type: "danger" });
            return;
        }
        await l10nVeFiscalSerialExecuteReport({
            env: this.env,
            action,
        });
    }
}

registry.category("view_widgets").add("l10n_ve_fiscal_serial_report_button", {
    component: FiscalReportButton,
    extractProps: ({ attrs }) => ({
        action: attrs.action,
        button_class: attrs.button_class,
    }),
});
