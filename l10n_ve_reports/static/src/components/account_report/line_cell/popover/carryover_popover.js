/** @odoo-module */

import {useService} from "@web/core/utils/hooks";
import { Component, t, usePlugin, useProps } from "@odoo/owl";
import { ActionPlugin } from "@web/webclient/actions/action_plugin";

export class AccountReportCarryoverPopover extends Component {
    static template = "l10n_ve_reports.AccountReportCarryoverPopover";
    props = useProps({
        close: t.function(),
        carryoverData: t.object(),
        options: t.object(),
        context: t.object(),
    });

    setup() {
        this.actionService = usePlugin(ActionPlugin);
        this.orm = useService("orm");
    }

    //------------------------------------------------------------------------------------------------------------------
    //
    //------------------------------------------------------------------------------------------------------------------
    async viewCarryoverLinesAction(expressionId, columnGroupKey) {
        const viewCarryoverLinesAction = await this.orm.call(
            "account.report.expression",
            "action_view_carryover_lines",
            [expressionId, this.props.options, columnGroupKey],
            {
                context: this.props.context,
            }
        );
        this.props.close();
        return this.actionService.doAction(viewCarryoverLinesAction);
    }
}
