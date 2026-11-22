/** @odoo-module */

import {useAutofocus, useService} from "@web/core/utils/hooks";

import { Component, signal, t, useProps } from "@odoo/owl";

export class AccountReportEditPopover extends Component {
    static template = "l10n_ve_reports.AccountReportEditPopover";
    props = useProps({
        line_id: t.string(),
        cell: t.object(),
        controller: t.object(),
        onClose: t.function(),
        close: t.function(),
    });

    setup() {
        this.orm = useService("orm");

        if (this.props.cell.figure_type === "boolean") {
            this.booleanTrue = signal.ref();
            this.booleanFalse = signal.ref();
        } else {
            this.input = signal.ref();
            useAutofocus({ref: this.input});
        }
    }

    // -----------------------------------------------------------------------------------------------------------------
    // Edit
    // -----------------------------------------------------------------------------------------------------------------
    async edit() {
        let editValue;
        const editPopupData = JSON.parse(this.props.cell.edit_popup_data);

        if (this.props.cell.figure_type === "boolean")
            editValue = Number(
                this.booleanTrue().checked && !this.booleanFalse().checked
            );
        else editValue = this.input().value;

        const res = await this.orm.call(
            "account.report",
            "action_modify_manual_value",
            [
                this.props.controller.options.report_id,
                this.props.line_id,
                this.props.controller.options,
                editPopupData.column_group_key,
                editValue,
                editPopupData.target_expression_id,
                editPopupData.rounding,
                this.props.controller.columnGroupsTotals,
            ],
            {
                context: this.props.controller.context,
            }
        );

        this.props.controller.lines = res.lines;
        this.props.controller.columnGroupsTotals = res.column_groups_totals;

        this.props.onClose();
    }
}
