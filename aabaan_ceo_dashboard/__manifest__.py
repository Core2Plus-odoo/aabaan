# Part of the Aabaan Odoo build by C2P Consultants FZC LLC.
{
    'name': 'Aabaan CEO Dashboard',
    'version': '19.0.1.2.0',
    'category': 'Reporting',
    'summary': 'Live, drillable executive dashboard: contract book, renewals, visits, pipeline, receivables',
    'description': """
A native CEO dashboard for Aaban Classic Building Cleaning L.L.C.

- Contract book (confirmed orders): gross/net value, count, split by service
  line and emirate regime.
- Renewal pipeline: value past end-of-term (critical), next 90 days, later,
  open-ended.
- Field service: visits by type (routine / follow-up / complaint), scheduled
  next 30 days, overdue, SLA breaches.
- Sales pipeline and posted receivables with overdue split.

Every tile and bar drills into the underlying records as a filtered list
view. All aggregation is batched (_read_group); the database-defined x_*
fields are resolved at runtime and the dashboard degrades gracefully when a
field or module is absent. Menu: CEO Dashboard (sales managers).
""",
    'author': 'C2P Consultants FZC LLC',
    'license': 'OPL-1',
    'depends': [
        'aabaan_visit_schedule',
        'sale_subscription',
        'crm',
    ],
    'data': [
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'aabaan_ceo_dashboard/static/src/**/*',
        ],
    },
    'installable': True,
    'application': True,
}
