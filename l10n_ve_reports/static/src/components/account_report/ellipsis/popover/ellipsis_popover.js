/** @odoo-module */

import { Component, t, useProps } from "@odoo/owl";

export class AccountReportEllipsisPopover extends Component {
    static template = "l10n_ve_reports.AccountReportEllipsisPopover";
    props = useProps({
        close: t.function(),
        name: t.string(),
        copyEllipsisText: t.function(),
    });
}
