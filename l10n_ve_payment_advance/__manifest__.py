{
    "name": "Venezuela - Anticipos de clientes y proveedores en pagos",
    "version": "20.0.1.0.0",
    "category": "Accounting/Localizations",
    "author": "andyengit, Odoo Community Association (OCA)",
    "maintainers": ["andyengit"],
    "website": "https://github.com/OCA/l10n-venezuela",
    "license": "AGPL-3",
    "depends": ["account"],
    "data": [
        "views/res_partner_views.xml",
        "views/res_config_settings_views.xml",
        "views/account_payment_register_views.xml",
        "views/account_move_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "l10n_ve_payment_advance/static/src/components/account_advance_payment_field/**/*",
        ],
    },
    "installable": True,
}
