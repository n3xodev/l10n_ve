import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { proxy } from "@odoo/owl";
import { AccountReportFilters } from "@account_reports/components/account_report/filters/filters";

const { DateTime } = luxon;

patch(AccountReportFilters.prototype, {
    setup() {
        super.setup(...arguments);
        this.currencyDateLoadingState = proxy({ isLoading: false });
    },

    get selectedDisplayCurrencyName() {
        const options = this.controller.cachedFilterOptions();
        const displayCurrency = options.display_currency;
        if (displayCurrency) {
            return `${displayCurrency.symbol || displayCurrency.name}`;
        }
        const companyCurrency = options.companies?.[0]?.currency_id;
        if (companyCurrency) {
            const currency = options.available_currencies?.find(
                (c) => c.id === companyCurrency
            );
            if (currency) {
                return `${currency.symbol || currency.name}`;
            }
        }
        return _t("Currency");
    },

    get selectedCurrencyRateDateTypeName() {
        const options = this.controller.cachedFilterOptions();
        const dateType = options.currency_rate_date_type || "current";
        return this.currencyRateDateTypeLabel(dateType);
    },

    currencyRateDateTypeLabel(dateType) {
        const dateTypeNames = {
            current: _t("Fecha Actual"),
            document: _t("Fecha del Documento"),
            manual: _t("Seleccionar Fecha"),
        };
        return dateTypeNames[dateType] || dateTypeNames.current;
    },

    get currencyRateDateValue() {
        const date = this.controller.cachedFilterOptions().currency_rate_date;
        if (date) {
            return DateTime.fromISO(date);
        }
        return DateTime.now();
    },

    async filterDisplayCurrency(currencyId) {
        await this.controller.updateOption("display_currency_id", currencyId, false);
        this.currencyDateLoadingState.isLoading = true;
        try {
            await this.controller.reload(
                "display_currency_id",
                this.controller.cachedFilterOptions()
            );
        } finally {
            this.currencyDateLoadingState.isLoading = false;
        }
    },

    async filterCurrencyRateDateType(dateType) {
        await this.controller.updateOption("currency_rate_date_type", dateType, false);
        if (
            dateType === "manual" &&
            !this.controller.cachedFilterOptions().currency_rate_date
        ) {
            const today = DateTime.now();
            await this.controller.updateOption(
                "currency_rate_date",
                today.toISODate(),
                false
            );
        }
        this.currencyDateLoadingState.isLoading = true;
        try {
            await this.controller.reload(
                "currency_rate_date_type",
                this.controller.cachedFilterOptions()
            );
        } finally {
            this.currencyDateLoadingState.isLoading = false;
        }
    },

    async onCurrencyRateDateChanged(date) {
        if (!date) {
            return;
        }

        let dateStr;
        if (date instanceof DateTime) {
            dateStr = date.toISODate();
        } else if (date instanceof Date) {
            dateStr = date.toISOString().split("T")[0];
        } else if (typeof date === "string") {
            dateStr = date;
        } else {
            try {
                dateStr = DateTime.fromJSDate(date).toISODate();
            } catch {
                return;
            }
        }

        if (!dateStr) {
            return;
        }

        this.currencyDateLoadingState.isLoading = true;
        try {
            await this.controller.updateOption("currency_rate_date", dateStr, false);
            await this.controller.reload(
                "currency_rate_date",
                this.controller.cachedFilterOptions()
            );
        } finally {
            this.currencyDateLoadingState.isLoading = false;
        }
    },
});
