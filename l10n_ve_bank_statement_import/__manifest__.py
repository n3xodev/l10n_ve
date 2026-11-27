{
    "name": "Venezuela Bank Statement Import",
    "icon": "/poweredbyandy_saas/static/description/icon.png",
    "summary": "Importación de estados de cuenta bancarios para Venezuela",
    "version": "20.0.1.0.0",
    "category": "Accounting",
    "website": "https://github.com/OCA/l10n-venezuela",
    "author": "andyengit",
    "maintainers": ["andyengit"],
    "license": "AGPL-3",
    "depends": [
        "account_statement_import_sheet_file",
    ],
    "excludes": [
        "account_accountant",
    ],
    "data": [
        "data/map_data.xml",
        "views/account_statement_import_sheet_mapping_views.xml",
    ],
    "installable": True,
}
