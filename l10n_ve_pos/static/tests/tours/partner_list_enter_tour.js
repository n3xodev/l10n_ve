import * as Dialog from "@point_of_sale/../tests/generic_helpers/dialog_util";
import * as Chrome from "@point_of_sale/../tests/pos/tours/utils/chrome_util";
import * as ProductScreen from "@point_of_sale/../tests/pos/tours/utils/product_screen_util";
import { registry } from "@web/core/registry";

const INPUT = ".modal-dialog .input-group input";
const ROW = ".partner-list .partner-info";

function typeQueryAndPressEnter(value) {
    return [
        {
            content: `Type "${value}" in the partner search`,
            trigger: INPUT,
            run: `edit ${value}`,
        },
        {
            content: "Wait for the search debounce",
            trigger: INPUT,
            run: async () => {
                await new Promise((resolve) => setTimeout(resolve, 400));
            },
        },
        {
            content: "Press Enter",
            trigger: INPUT,
            run: () => {
                document
                    .querySelector(INPUT)
                    .dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, key: "Enter" }));
            },
        },
    ];
}

registry.category("web_tour.tours").add("L10nVePartnerListEnterLocalTour", {
    steps: () =>
        [
            Chrome.startPoS(),
            Dialog.confirm("Open Register"),
            ProductScreen.clickPartnerButton(),
            // One local match: Enter selects it.
            ...typeQueryAndPressEnter("Zxq Unico"),
            ProductScreen.customerIsSelected("AAA Zxq Unico Cliente"),
            // Several local matches: Enter keeps the list and reports the count.
            ProductScreen.clickPartnerButton(),
            ...typeQueryAndPressEnter("Zxq Doble"),
            {
                content: "The notification reports the matches",
                trigger: '.o_notification:contains("2 customer(s) found")',
            },
            {
                content: "Both partners stay listed",
                trigger: `${ROW}:contains("Zxq Doble Uno")`,
            },
            {
                content: "Both partners stay listed (second)",
                trigger: `${ROW}:contains("Zxq Doble Dos")`,
            },
        ].flat(),
});

registry.category("web_tour.tours").add("L10nVePartnerListEnterServerTour", {
    steps: () =>
        [
            Chrome.startPoS(),
            Dialog.confirm("Open Register"),
            ProductScreen.clickPartnerButton(),
            // No local match: Enter searches the server and selects the single result.
            ...typeQueryAndPressEnter("ZZZ Zxq Lejano"),
            ProductScreen.customerIsSelected("ZZZ Zxq Lejano"),
        ].flat(),
});
