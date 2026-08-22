# Aabaan Legal Entities

The emirate presences are **separate legal entities**, per the trade
licence documents — not branches. Configuration-only module.

## The entities (facts from the licences)

| Company | Legal form | Licence | Expires | Address |
|---|---|---|---|---|
| Aaban Classic Building Cleaning L.L.C. (main) | LLC, Ajman DED | 103074 | 08-Jan-2027 | Shop 2, Al Nuaimiya 1, Ajman |
| Aaban Classic Building Cleaning — Dubai | Sole Establishment, Dubai DET | 989256 | 13-Oct-2026 | Office 126, Bin Salloum Bldg, Hor Al Anz, Deira |
| Aaban Classic Building Cleaning — SHJ BR 2 | Services Agency, Sharjah EDD | 908692 | 01-Jul-2026 ⚠ | Shop 1-2, Al Sharq St, Al Butina |

⚠ The provided Sharjah document shows an already-past expiry; if renewed,
update the date on the company form (or provide the renewed licence).

The letterhead's old "109374" appears on **none** of the licences and is
treated as a known-wrong value: it is replaced by 103074 wherever found,
and the website prints the live company registry instead of hardcoding.

## What the setup does (idempotent, on install/upgrade)

- Detaches the former Dubai/Sharjah branch companies into standalone
  entities with their licence facts, loading the UAE chart of accounts
  when possible (otherwise configure it once in Accounting settings).
- Archives the empty UAQ / RAK companies (recoverable; the Emirate
  analytic dimension still tracks any UAQ/RAK jobs).
- Fixes placeholder head-office contact data; grants entity access to
  head-office users.
- Seeds **Trade Licence Expiry** on each company; a daily check raises a
  renewal activity 60 days ahead (no duplicates).

## What is configuration (native Odoo)

- Per-entity bank accounts and journals, users' default company, and the
  Dubai/Sharjah charts if auto-load was not possible.
- Fujairah: no licence provided — no entity created. Say the word when
  one exists.

## Fixed: registry-crashing load-order bug

The module now depends on `account`. Creating a `res.company` also creates
its `res.partner`; `account` adds a NOT-NULL field to `res.partner`
(`autopost_bills`). Without a declared dependency, Odoo's module load order
isn't guaranteed to load `account` before this module, so the ORM didn't
know that field existed yet when the entity-creation migration ran —
the INSERT omitted it, Postgres rejected the null, and the whole registry
failed to load (not just this module). The company-create call is also
now wrapped the same way every other write in this function already is:
logged and skipped on failure, never able to take the database down.
