import { _t } from "@web/core/l10n/translation";
import { AccountReportController } from "@account_reports/components/account_report/controller";
import { AccountReportFilters } from "@account_reports/components/account_report/filters/filters";

export class DailyPaymentsReportFilters extends AccountReportFilters {
    static template = "l10n_ve_reports_enterprise.DailyPaymentsReportFilters";

    get dailyPaymentsDateTypeLabel() {
        return this.dailyPaymentsDateTypeOptionLabel(
            this.controller.cachedFilterOptions().daily_payments_date_type || "validation"
        );
    }

    dailyPaymentsDateTypeOptionLabel(dateType) {
        if (dateType === "payment") {
            return _t("Fecha del pago");
        }
        return _t("Fecha de validación");
    }

    async filterDailyPaymentsDateType(dateType) {
        if (this.controller.cachedFilterOptions().daily_payments_date_type === dateType) {
            return;
        }
        await this.controller.updateOption("daily_payments_date_type", dateType, false);
        await this.controller.reload(
            "daily_payments_date_type",
            this.controller.cachedFilterOptions()
        );
    }
}

AccountReportController.registerCustomComponent(DailyPaymentsReportFilters);
