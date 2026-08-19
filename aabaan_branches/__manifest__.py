# Part of the Aabaan Odoo build by C2P Consultants FZC LLC.
{
    'name': 'Aabaan Emirate Branches',
    'version': '19.0.1.0.0',
    'post_init_hook': '_post_init_hook',
    'category': 'Hidden/Tools',
    'summary': 'Seeds the four emirate branches under the head office (native Odoo branches)',
    'description': """
Configuration-only module — no models, no views.

Creates the four emirate branches as native Odoo company branches under
the head office (the main company, Ajman): Sharjah, Dubai, Umm Al Quwain
and Ras Al Khaimah. Together with the Ajman head office that covers all
five emirates of operation.

Native branch behaviour (nothing custom): branches share the head
office's chart of accounts, taxes and fiscal settings; each branch can
carry its own address, trade licence and bank account, and documents can
be issued under the branch header via the company switcher. Every user
who can see the head office is given access to the branches.

The seeding is idempotent — re-installing or re-running never duplicates
a branch (matched by emirate name). Licence/TRN details per branch are
deliberately left blank until the business provides them.
""",
    'author': 'C2P Consultants FZC LLC',
    'license': 'OPL-1',
    'depends': ['base'],
    'data': [],
    'installable': True,
    'application': False,
}
