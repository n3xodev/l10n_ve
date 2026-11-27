# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Venezuelan Reports - Stock Inventory Book",
    "version": "20.0.1.0.0",
    "icon": "/poweredbyandy_saas/static/description/icon.png",
    "summary": "Libro de Inventario para reportes SENIAT",
    "category": "Inventory/Inventory",
    "author": "andyengit",
    "maintainers": ["andyengit"],
    "description": """
Libro de Inventario
===================
Entradas y salidas de inventarios según Reglamento ISLR Art. 177.
    """,
    "depends": [
        "l10n_ve_reports",
        "l10n_ve_reports_stock_base",
        "stock",
        "l10n_ve_seniat",
    ],
    "data": [
        "data/inventory_book_report.xml",
        "data/inventory_book_report_actions.xml",
        "views/seniat_menuitems.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "l10n_ve_reports_stock/static/src/components/inventory_book_report/*.js",
            "l10n_ve_reports_stock/static/src/components/inventory_book_report/*.xml",
        ],
    },
    "installable": True,
    "license": "OEEL-1",
}
