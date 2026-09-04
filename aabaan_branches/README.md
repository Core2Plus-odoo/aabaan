# Aabaan Branches

One company, several branches. Ajman (head office), Dubai and Sharjah are
run as **branches of the single Aaban company**, not as separate companies
in Odoo.

## What is code, what is configuration

**Configuration (lives in the production database):**

- The **Emirate analytic plan** and its accounts. This is the branch
  dimension. It is defined in the database, not in this repo (Rule 2), and
  is resolved at runtime by name. `aabaan_finance_core` already autofills
  it on invoice lines and enforces it on every posting.

**Code (this module):**

- `Trade Licence No.` and `Trade Licence Expiry` on each Emirate analytic
  account, so a branch's licence is tracked where the branch is.
- A daily check raising **one** open renewal activity 60 days before
  expiry — for the company licence and for every branch licence. An open
  activity blocks duplicates, so an expired licence does not re-alert
  daily.
- A **Branch** field on `sale.order`, searchable and groupable, pointing at
  an Emirate analytic account.
- Head-office contact data corrected from the letterhead where Odoo's demo
  placeholders were still in place.

## Why the branch drives the analytic tag

`aabaan_finance_core` fills the Emirate analytic tag on an invoice line by
reading the source contract's `x_emirate_regime` label and matching it
against analytic account names. That fuzzy step is what leaves a posting
blocked when no name matches.

When a contract names its Branch explicitly, finance core uses that link
instead and skips the matching. The lookup is runtime-guarded
(`'aabaan_branch_id' in order._fields`) because `aabaan_finance_core` does
not depend on this module, so it degrades to the old behaviour if this
module is absent.

## Licence facts

Transcribed from the licence documents; no figure is invented.

| Branch | Licence | Expires |
|---|---|---|
| Ajman (head office) | 103074 | 08-Jan-2027 |
| Dubai | 989256 | 13-Oct-2026 |
| Sharjah | 908692 | 01-Jul-2026 |

The letterhead's old registry **109374** appears on none of the licence
documents and is treated as a known-wrong placeholder, corrected wherever
it was used.

## Migrating from separate companies

Versions 19.0.2.x split Dubai and Sharjah into **standalone companies**.
Version 19.0.3.0.0 reverses that direction: the emirates are branches
again.

The upgrade **stops maintaining the split** and carries each company's
licence number and expiry onto the matching branch, so nothing is lost.
It does **not** archive or merge those companies, because:

> Odoo cannot move journal entries between companies.

Consolidating the books is an accounting exercise, not a migration. The
post-migration logs a warning naming any company still standing. Deciding
what to do with them is a finance decision, and it has real consequences:

- **If each emirate files its own VAT return** under its own TRN, they must
  stay separate legal entities for accounting, whatever the operational
  reporting looks like. In that case keep the companies and use the branch
  dimension only for operational grouping.
- **If the group files once** under the head-office TRN, the emirate
  companies can be wound down: stop posting to them, close their periods,
  and carry balances across with journal entries booked in the surviving
  company. Then archive them — never delete, so the history stays
  auditable.

Whichever applies, the branch dimension in this module is unaffected: it
groups contracts, invoices and reporting by emirate either way.
