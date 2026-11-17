# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Venezuelan Reports - SENIAT Fiscal Books",
    "version": "20.0.1.0.0",
    "icon": "/poweredbyandy_saas/static/description/icon.png",
    "website": "https://github.com/nexo-ve/l10n_ve",
    "summary": "SENIAT fiscal-book reports bridge for the Venezuelan localization",
    "category": "Accounting/Localizations",
    "author": "andyengit",
    "maintainers": ["andyengit"],
    "countries": ["ve"],
    "description": """
SENIAT Fiscal Books
====================

Bridge module between the generic accounting reports engine
(``l10n_ve_reports``) and the Venezuelan localization
(``l10n_ve_seniat``, ``l10n_ve_withholding``).

Contains the SENIAT fiscal-book reports (sales book, purchases book,
fiscal-machine sales book, report X) and their menus, which require
Venezuelan-specific accounting data and therefore cannot live in the
generic reports engine.

Auto-installs as soon as ``l10n_ve_reports``, ``l10n_ve_seniat`` and
``l10n_ve_withholding`` are all present in the database, so existing
Venezuelan installations keep the exact same reports and menus with
no manual step required.
    """,
    "depends": ["l10n_ve_reports", "l10n_ve_seniat", "l10n_ve_withholding"],
    "auto_install": True,
    "license": "OEEL-1",
    "data": [
        "data/report_x.xml",
        "data/sales_book_report.xml",
        "data/sales_book_fiscal_machine_report.xml",
        "data/purchases_book_report.xml",
        "data/seniat_report_actions.xml",
        "data/menuitems.xml",
        "data/seniat_reports_menuitems.xml",
    ],
    "assets": {
        "l10n_ve_reports.assets_pdf_export": [
            "l10n_ve_reports_seniat/static/src/scss/sales_book_report.scss",
        ],
    },
}
