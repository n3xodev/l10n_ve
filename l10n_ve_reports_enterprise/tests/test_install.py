# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestL10nVeReportsEnterpriseInstall(TransactionCase):
    """Verify reports, client actions, menus, assets, and menu rules in EE."""

    REPORTS = (
        ("diary_book_report", "l10n_ve.diary.book.report.handler"),
        ("bank_book_report", "l10n_ve.bank.book.report.handler"),
        ("cash_book_report", "l10n_ve.cash.book.report.handler"),
        ("daily_payments_report", "l10n_ve.daily.payments.report.handler"),
        ("purchases_book_report", "l10n_ve.purchase.book.report.handler"),
        ("sales_book_report", "l10n_ve.sales.book.report.handler"),
        (
            "sales_book_fiscal_machine_report",
            "l10n_ve.sales.book.fiscal.machine.report.handler",
        ),
        ("ve_report_x", "l10n_ve.report_x.handler"),
    )

    ACTIONS = (
        "action_account_report_diary_book",
        "action_account_report_bank_book",
        "action_account_report_cash_book",
        "action_account_report_daily_payments",
        "action_account_report_ve_report_x",
        "action_account_report_sales_book",
        "action_account_report_sales_book_fiscal_machine",
        "action_account_report_purchases_book",
    )

    SENIAT_MENUS = (
        "menu_seniat_report_general_ledger",
        "menu_seniat_report_bank_book",
        "menu_seniat_report_cash_book",
        "menu_seniat_report_diary_book",
        "menu_seniat_report_daily_payments",
        "menu_seniat_report_ve_report_x",
        "menu_seniat_report_sales_book",
        "menu_seniat_report_purchases_book",
        "menu_seniat_report_sales_book_fiscal_machine",
    )

    AUDIT_MENUS = (
        "menu_action_account_report_diary_book",
        "menu_action_account_report_bank_book",
        "menu_action_account_report_cash_book",
        "menu_action_account_report_daily_payments",
        "menu_action_account_report_ve_report_x",
        "menu_action_account_report_sales_book",
        "menu_action_account_report_sales_book_fiscal_machine",
        "menu_action_account_report_purchases_book",
    )

    def test_reports_registered_with_enterprise_handlers(self):
        for xml_id, handler_name in self.REPORTS:
            with self.subTest(report=xml_id):
                report = self.env.ref(f"l10n_ve_reports_enterprise.{xml_id}")
                self.assertEqual(report.custom_handler_model_name, handler_name)
                self.assertTrue(report.column_ids)

    def test_client_actions_use_native_account_report_tag(self):
        for xml_id in self.ACTIONS:
            with self.subTest(action=xml_id):
                action = self.env.ref(f"l10n_ve_reports_enterprise.{xml_id}")
                self.assertEqual(action.tag, "account_report")

    def test_seniat_and_audit_menuitems_exist(self):
        seniat_root = self.env.ref("l10n_ve_seniat.menu_seniat_reports")
        audit_root = self.env.ref("account.account_audit_control_menu")
        for xml_id in self.SENIAT_MENUS:
            with self.subTest(seniat_menu=xml_id):
                menu = self.env.ref(f"l10n_ve_reports_enterprise.{xml_id}")
                self.assertEqual(menu.parent_id, seniat_root)
        for xml_id in self.AUDIT_MENUS:
            with self.subTest(audit_menu=xml_id):
                menu = self.env.ref(f"l10n_ve_reports_enterprise.{xml_id}")
                self.assertEqual(menu.parent_id, audit_root)

    def test_pdf_scss_assets_registered(self):
        bundle = self.env["ir.qweb"]._get_asset_bundle(
            "account_reports.assets_pdf_export", css=True, js=False
        )
        asset_paths = [asset.url for asset in bundle.stylesheets]
        self.assertTrue(
            any("sales_book_report.scss" in p for p in asset_paths),
            "sales_book_report.scss must be in account_reports.assets_pdf_export",
        )
        self.assertTrue(
            any("daily_payments_report_pdf.scss" in p for p in asset_paths),
            "daily_payments_report_pdf.scss must be in account_reports.assets_pdf_export",
        )

    def test_fiscal_machine_menu_visibility_rule(self):
        rules = self.env["ir.ui.menu"]._l10n_ve_emission_medium_menu_rules()
        self.assertIn(
            "l10n_ve_reports_enterprise.menu_seniat_report_sales_book_fiscal_machine",
            rules.get("fiscal_machine", ()),
        )
