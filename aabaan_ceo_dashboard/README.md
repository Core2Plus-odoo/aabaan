# Aabaan CEO Dashboard (`aabaan_ceo_dashboard`)

A native, live, drillable executive dashboard inside Odoo. Menu: **CEO
Dashboard** (visible to sales managers). Styled after the Aaban Services
letterhead — ink masthead with the orange slash.

## What it shows (all live from the database)

- **Contracted book** — confirmed sale orders: gross, net of VAT, count;
  split by service line (`x_service_line`) and emirate regime
  (`x_emirate_regime`).
- **Open quotations** and the **CRM pipeline** (open leads/opportunities and
  expected revenue).
- **Renewal pipeline** — contract value **past end-of-term** (critical),
  next 90 days, beyond, and open-ended, from `sale_subscription`'s
  `end_date`.
- **Field service** — visits by type (routine / follow-up / complaint),
  visits scheduled in the next 30 days, visits past their planned date, and
  SLA-deadline breaches (`x_sla_due`).
- **Receivables** — posted customer invoices outstanding, with the overdue
  slice, and the customer count.
- **Client industry split** — the book grouped by the customer's Industry
  (`res.partner.industry_id`; set it on the contact or map it at import).
- **Contract size mix** — five value bands from micro-contracts to majors.
- **Month-by-month renewal timeline** — overdue, the next 12 calendar
  months, and the tail, under the headline renewal buckets.
- **F&B premises count** (Dubai LO 11 flag from the visit module).

**Every tile, bar and chip is a drill-down**: it opens the underlying
records as a filtered list view, so the number on screen is always one
click from its evidence.

## Design notes

- Data provider: `aabaan.ceo.dashboard` (AbstractModel), one `get_data()`
  call, all aggregation batched via `_read_group` — no per-record loops.
- The manual `x_*` fields are runtime-resolved (same policy as the other
  Aabaan modules): a missing field collapses its section into an honest
  empty state instead of erroring, so the module installs on a bare
  database.
- Frontend: OWL client action (`static/src/dashboard.js|xml|scss`), no
  external libraries.
- Numbers respect record rules: the dashboard shows what the logged-in
  manager is allowed to see, because every figure is computed with their
  access rights.

## Relation to the web dashboard artifact

The claude.ai artifact ("Aaban — CEO Dashboard") is a snapshot of the
pre-migration master data sheet. This module is the live system view — it
starts near-zero on the clean database and fills as contracts, visits and
invoices are created.
