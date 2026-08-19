# Aabaan Website Theme

Code-defined, booking-first website for Aaban Classic Building Cleaning
L.L.C., in the approved Urban Company / Justlife style.

## What is code (this module)

| Piece | Where |
|---|---|
| Homepage at `/` (hero, chips, trust bar, service tiles, 3 steps, AMC + coverage) | `views/home_page.xml` |
| `/services` overview | `views/services_index.xml` |
| `/services/pest-control`, `/services/water-tank`, `/services/anti-termite`, `/services/deep-cleaning` | `views/service_pages.xml` |
| `/about` (licence, approvals, numbers from the contract master sheet), `/faq` | `views/about_page.xml`, `views/faq_page.xml` |
| Site-wide footer (replaces `website.footer_custom`) + fixed mobile action bar | `views/layout.xml` |
| 301 redirect `/home-v2 → /` (`website.rewrite`) | `views/layout.xml` |
| All styling — brand ink `#17171a`, orange `#ef7d25`, navbar, buttons | `static/src/scss/aabaan_theme.scss` |
| Homepage switch-over + menu build (idempotent, shared by install hook and migration) | `__init__.py` |

The switch-over parks any previous page at `/` to `/home-classic`
(unpublished, never deleted), clears `website.homepage_url`, and completes
each website's main menu — Home, Services (dropdown), About us, FAQ,
Contact, Book a visit — matching existing items by URL so client-added
menu entries are never touched.

## What is configuration (native Odoo, not this module)

- The contact page is the native `/contactus` form (`website_crm`) — leads
  land in CRM as before.
- All pages stay editable in the website builder afterwards.
- If the live website had a builder-customised footer, that website-specific
  copy can shadow the branded footer — reset the footer template in the
  builder to pick this one up.
- Facts on `/about` come from the trade licence and the contract master
  sheet (600+ contracts, 4,500+ visits/year); update them there when the
  business numbers move.
