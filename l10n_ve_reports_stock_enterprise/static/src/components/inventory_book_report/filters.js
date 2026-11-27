import { _t } from "@web/core/l10n/translation";
import { AccountReportController } from "@account_reports/components/account_report/controller";
import { AccountReportFilters } from "@account_reports/components/account_report/filters/filters";

export class InventoryBookReportFilters extends AccountReportFilters {
    static template = "l10n_ve_reports_stock_enterprise.InventoryBookReportFilters";

    get selectedWarehouseName() {
        const warehouseIds = this.controller.cachedFilterOptions().warehouse_ids || [];
        if (!warehouseIds.length) {
            return _t("Todos los almacenes");
        }
        if (warehouseIds.length === 1) {
            return _t("1 almacén");
        }
        return _t("%s almacenes", warehouseIds.length);
    }
}

AccountReportController.registerCustomComponent(InventoryBookReportFilters);
