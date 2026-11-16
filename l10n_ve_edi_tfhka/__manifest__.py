{
    "name": "Venezuela TFHKA EDI",
    "summary": "Conector The Factory HKA para facturacion digital Venezuela",
    "version": "20.0.1.0.0",
    "category": "Accounting/Localizations",
    "author": "andyengit",
    "maintainer": "andyengit",
    "website": "https://github.com/OCA/l10n-venezuela",
    "license": "LGPL-3",
    "depends": ["l10n_ve_edi", "l10n_ve_stock", "l10n_ve_withholding", "l10n_ve_igtf"],
    "assets": {
        "web.assets_frontend": [
            "l10n_ve_edi_tfhka/static/src/js/portal_invoice_pdf_iframe.js",
        ],
    },
    "data": [
        "views/res_config_settings_views.xml",
        "views/account_journal_views.xml",
        "views/account_move_views.xml",
        "views/account_retention_views.xml",
        "views/portal_templates.xml",
    ],
    "installable": True,
    "application": False,
}
