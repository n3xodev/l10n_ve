{
    "name": "Venezuela SENIAT - Enterprise Inventory Book",
    "version": "20.0.1.0.0",
    "category": "Inventory/Localizations",
    "summary": "Native Odoo 20 Enterprise Inventory Book (ISLR Art. 177) for Venezuela",
    "author": "Nexodev",
    "license": "OEEL-1",
    "depends": [
        "account_reports",
        "stock",
        "l10n_ve_seniat",
        "l10n_ve_reports_stock_base",
    ],
    "excludes": ["l10n_ve_reports", "l10n_ve_reports_stock"],
    "auto_install": ["account_reports", "stock", "l10n_ve_seniat"],
    "data": [
        "data/inventory_book_report.xml",
        "data/inventory_book_report_actions.xml",
        "views/seniat_menuitems.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "l10n_ve_reports_stock_enterprise/static/src/components/inventory_book_report/filters.js",
            "l10n_ve_reports_stock_enterprise/static/src/components/inventory_book_report/filters.xml",
        ],
    },
    "installable": True,
}
