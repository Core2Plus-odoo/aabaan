# Part of the Aabaan Odoo build by C2P Consultants FZC LLC.
{
    'name': 'Aabaan Legal Entities',
    'version': '19.0.2.2.0',
    'post_init_hook': '_post_init_hook',
    'category': 'Hidden/Tools',
    'summary': 'The three licensed Aaban entities as separate companies, with licence expiry tracking',
    'description': """
Configuration module carrying the legal structure from the trade licence
documents — three separate legal entities, not branches:

- Aaban Classic Building Cleaning L.L.C. (Ajman) — the main company;
  licence 103074, expiring 08-Jan-2027. The letterhead's old "109374"
  appears on none of the licences and is corrected wherever it was used.
- Aaban Classic Building Cleaning — Dubai (Sole Establishment);
  licence 989256, expiring 13-Oct-2026.
- Aaban Classic Building Cleaning — SHJ BR 2 (Services Agency);
  licence 908692 — the provided document shows expiry 01-Jul-2026:
  if renewed, update the date on the company form.

The idempotent setup detaches the former Dubai/Sharjah branch companies
into standalone entities (loading the UAE chart when possible), archives
the empty UAQ / RAK companies (recoverable), fixes placeholder head
office contact data, and grants entity access to head-office users.

Adds a Trade Licence Expiry date on every company with a daily check
that raises a renewal activity 60 days ahead.
""",
    'author': 'C2P Consultants FZC LLC',
    'license': 'OPL-1',
    'depends': ['base', 'mail'],
    'data': [
        'data/cron.xml',
        'views/res_company_views.xml',
    ],
    'installable': True,
    'application': False,
}
