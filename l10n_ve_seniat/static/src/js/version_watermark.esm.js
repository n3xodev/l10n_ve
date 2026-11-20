/** @odoo-module **/

import {Component, useProps} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {session} from "@web/session";

class VersionLabel extends Component {
    static template = "l10n_ve_seniat.VersionLabel";
    props = useProps();

    setup() {
        this.version = session.l10n_ve_version || "";
    }
}

registry.category("main_components").add("l10n_ve_version_label", {
    Component: VersionLabel,
});
