/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { DashboardKanbanRenderer } from "@account/views/account_dashboard_kanban/account_dashboard_kanban_renderer";
import { EdiSeniatInvoiceDashboard } from "../../components/edi_seniat_invoice_dashboard/edi_seniat_invoice_dashboard";

patch(DashboardKanbanRenderer.components, {
    EdiSeniatInvoiceDashboard,
});
