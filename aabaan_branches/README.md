# Aabaan Emirate Branches

Configuration-only module. Seeds the company structure for the five
emirates of operation using **native Odoo branches** — no models, no
views, no custom logic.

## What is code (this module)

- An idempotent install hook that creates four branches under the head
  office (the main company, Ajman): **Sharjah, Dubai, Umm Al Quwain,
  Ras Al Khaimah** — each with UAE country, the matching emirate state
  and city. Existing branches are matched by emirate name and never
  duplicated.
- Every user who can already see the head office is granted access to
  the branches, so the company switcher shows them immediately.

## What is configuration (native Odoo, to be done in the UI)

- **Per-branch details**: trade licence number, TRN (if a branch has its
  own), address, phone and bank account — Settings → Users & Companies →
  Companies → open the branch. Left blank on purpose: those are business
  facts to be entered from the licence documents, not invented.
- **Issuing documents under a branch**: pick the branch in the company
  switcher (top right) before creating the quotation/invoice — native
  behaviour, branches share the head office's chart of accounts and
  taxes automatically.
- **Renaming**: branch names default to "<head office name> — <Emirate>";
  rename freely in the company form, the module matches by emirate word.

## Relation to the rest of the build

Branch companies and the **emirate analytic plan** (`aabaan_finance_core`)
are complementary: the analytic plan segments P&L by emirate on every
line regardless of which company issued the document; branches control
the legal header the document is issued under.
