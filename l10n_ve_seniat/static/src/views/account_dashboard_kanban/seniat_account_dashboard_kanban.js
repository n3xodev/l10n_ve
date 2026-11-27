/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { DashboardKanbanRenderer } from "@account/views/account_dashboard_kanban/account_dashboard_kanban_renderer";
import { SeniatInvoiceDashboard } from "../../components/seniat_invoice_dashboard/seniat_invoice_dashboard";

patch(DashboardKanbanRenderer.components, {
    SeniatInvoiceDashboard,
});
