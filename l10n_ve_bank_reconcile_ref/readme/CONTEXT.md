Depends on `account_reconcile_oca` (Odoo 19). The reference matching hooks into
`account.bank.statement.line._do_auto_reconcile_invoices()`. The reconcile
models of `account_reconcile_model_oca`, used by previous versions, are no
longer involved.
