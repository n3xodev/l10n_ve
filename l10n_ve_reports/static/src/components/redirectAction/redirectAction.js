/** @odoo-module */
import {registry} from "@web/core/registry";
import { Component, usePlugin } from "@odoo/owl";
import { ActionPlugin } from "@web/webclient/actions/action_plugin";
import {standardActionServiceProps} from "@web/webclient/actions/action_service";
import {Dialog} from "@web/core/dialog/dialog";

class RedirectAction extends Component {
    static template = "l10n_ve_reports.redirectAction";
    static components = {Dialog};

    static props = {
        ...standardActionServiceProps,
        action: Object,
    };

    setup() {
        this.actionService = usePlugin(ActionPlugin);
    }

    openClientAction() {
        this.actionService.doAction(this.props.action.params.depending_action);
    }

    close() {
        this.actionService.doAction({type: "ir.actions.act_window_close"});
    }
}

registry.category("actions").add("l10n_ve_reports.redirect_action", RedirectAction);
