/** @odoo-module */

import { Component, onMounted, proxy, signal, t, useProps } from "@odoo/owl";

export class AccountReportSearchBar extends Component {
    static template = "l10n_ve_reports.AccountReportSearchBar";
    props = useProps({
        initialQuery: t.string().optional(),
    });

    setup() {
        this.searchText = signal.ref();
        this.controller = proxy(this.env.controller);

        onMounted(() => {
            if (this.props.initialQuery) {
                this.searchText().value = this.props.initialQuery;
                this.search();
            }
        });
    }

    //------------------------------------------------------------------------------------------------------------------
    // Search
    //------------------------------------------------------------------------------------------------------------------
    search() {
        const inputText = this.searchText().value.trim();
        const query = inputText.toLowerCase();
        const linesIDsMatched = [];

        if (query.length) {
            for (const line of this.controller.lines) {
                if (!line.name) continue;

                const lineName = line.name.trim().toLowerCase();
                const match = lineName.indexOf(query) !== -1;

                if (match) {
                    linesIDsMatched.push(line.id);
                }
            }
            this.controller.lines_searched = linesIDsMatched;
            this.controller.updateOption("filter_search_bar", inputText);
        } else {
            delete this.controller.lines_searched;
            this.controller.deleteOption("filter_search_bar");
        }
    }
}
