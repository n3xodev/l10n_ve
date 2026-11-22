/** @odoo-module **/

import {_t} from "@web/core/l10n/translation";
import {localization} from "@web/core/l10n/localization";
import { NotificationPlugin } from "@web/core/notifications/notification_plugin";
import {useService} from "@web/core/utils/hooks";
import { Component, proxy, t, usePlugin, useProps } from "@odoo/owl";

import {AccountReportEllipsisPopover} from "@l10n_ve_reports/components/account_report/ellipsis/popover/ellipsis_popover";

export class AccountReportEllipsis extends Component {
    static template = "l10n_ve_reports.AccountReportEllipsis";
    props = useProps({
        name: t.string().optional(),
        no_format: t.any().optional(),
        type: t.string().optional(),
        maxCharacters: t.number(),
    });

    setup() {
        this.popover = useService("popover");
        this.notification = usePlugin(NotificationPlugin);
        this.controller = proxy(this.env.controller);
    }

    //------------------------------------------------------------------------------------------------------------------
    // Ellipsis
    //------------------------------------------------------------------------------------------------------------------
    get triggersEllipsis() {
        if (this.props.name) return this.props.name.length > this.props.maxCharacters;

        return false;
    }

    copyEllipsisText() {
        navigator.clipboard.writeText(this.props.name);
        this.notification.add(_t("Text copied"), {type: "success"});
        this.popoverCloseFn();
        this.popoverCloseFn = null;
    }

    showEllipsisPopover(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        if (this.popoverCloseFn) {
            this.popoverCloseFn();
            this.popoverCloseFn = null;
        }

        this.popoverCloseFn = this.popover.add(
            ev.currentTarget,
            AccountReportEllipsisPopover,
            {
                name: this.props.name,
                copyEllipsisText: this.copyEllipsisText.bind(this),
            },
            {
                closeOnClickAway: true,
                position: localization.direction === "rtl" ? "left" : "right",
            }
        );
    }
}
