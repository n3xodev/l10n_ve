/** @odoo-module */

import { Component, t, useProps } from "@odoo/owl";

export class AccountReportDebugPopover extends Component {
    static template = "l10n_ve_reports.AccountReportDebugPopover";
    props = useProps({
        close: t.function(),
        expressionsDetail: t.array(),
        onClose: t.function(),
    });
}
