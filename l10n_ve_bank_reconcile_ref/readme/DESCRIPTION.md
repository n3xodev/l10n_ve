Bank statements from Venezuelan banks (Banesco, Provincial, Mercantil, etc.)
often carry a reference longer than the one stored on the payment or the
invoice. Usually only the last 6 or 4 digits are the same.

This module extends the automatic reconciliation of `account_reconcile_oca`
for that case. It looks for an exact match of the reference digits and, when
there is none, for a match on the last digits (6 and then 4 by default). Open
payments of the same bank journal are searched before open invoices and bills. A statement line is
reconciled automatically only when there is a single candidate and its amount
matches the line exactly.
