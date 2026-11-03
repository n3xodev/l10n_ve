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
- Several candidates with the exact amount: the line is not reconciled. All
  the candidates are listed on the line in the reconcile widget and the
  Reconcile button stays disabled. Remove the entries that do not belong with
  the trash button; once a single entry covers the amount you can reconcile.
- An amount that does not match: the line is not reconciled. Choose the entry
  in the reconcile widget.

The **Clean** button of the reconcile widget resets the line and runs the
automatic reconciliation again, so the candidates are proposed again.
