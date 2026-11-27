# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Venezuela Reports Stock Base (Shared Mixins)",
    "version": "20.0.1.0.0",
    "summary": "Shared edition-agnostic inventory book mixin and warehouse configuration",
    "category": "Inventory/Localizations",
    "author": "andyengit",
    "maintainers": ["andyengit"],
    "license": "LGPL-3",
    "depends": [
        "l10n_ve_reports_base",
        "stock",
        "l10n_ve_seniat",
    ],
    "data": [
        "views/stock_warehouse_views.xml",
    ],
    "auto_install": False,
    "installable": True,
}
