# Copyright 2026 andyengit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Venezuela Bank Reconcile by Reference",
    "summary": "Auto-match bank statements by payment/invoice reference suffixes",
    "version": "19.0.2.0.0",
    "category": "Accounting",
    "website": "https://github.com/OCA/l10n-venezuela",
    "author": "andyengit, Odoo Community Association (OCA)",
    "maintainers": ["andyengit"],
    "license": "AGPL-3",
    "depends": [
        "account_reconcile_oca",
    ],
    "data": [
        "views/account_journal_views.xml",
    ],
    "installable": True,
}
