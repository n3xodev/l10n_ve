## Configuration

1. Go to **Accounting > Configuration > Journals** and open a bank journal.
2. In the **Reconcile by Reference** section set:
   - **Match by reference**: enables the feature on the journal (on by default).
   - **Suffix lengths**: lengths tried in order, for example `6,4`. Values
     below 4 are ignored.
   - **Match payments before invoices**: search open payments first, then
     open invoices and bills (on by default).

## Usage

Import the bank statement. Each statement line is processed by the OCA
automatic reconciliation first (reference contained in the reference or name
of the entry). Lines left over are matched by this module:

- The digits of the statement label and reference are normalized. Empty
  references, `0` and all-zero references are ignored.
- Candidates are searched by exact digits and then by each suffix length, in
  payments first and then in invoices and bills.
- If the line has a partner, only the entries of that partner are considered.
- Exactly one candidate whose open amount equals the line amount: the line is
  reconciled automatically. There is no tolerance, the amount must match.
- Several candidates, or an amount that does not match: the line is not
  reconciled. Choose the entry in the reconcile widget.
