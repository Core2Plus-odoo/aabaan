# Part of the Aabaan Odoo build by C2P Consultants FZC LLC.
{
    'name': 'Aabaan Website Theme',
    'version': '19.0.1.2.0',
    'post_init_hook': '_post_init_hook',
    'category': 'Website/Website',
    'summary': 'Booking-first homepage in the approved Urban Company / Justlife style',
    'description': """
Implements the approved website redesign concept as a code-defined page:

- New homepage at /home-v2 (the live homepage is untouched until the client
  sets the new page as homepage in the website builder — one click,
  reversible).
- Booking-first layout: hero with quick-pick service chips, trust bar
  (municipality approvals, MOCCAE pesticides, 10-year termite warranty, TRN),
  service tiles with real rate-card prices, 3-step booking strip, AMC and
  coverage panels, corrected contact details (800 AABAN, both mobiles,
  infoaabanservices@gmail.com — no landline) and a sticky mobile action bar
  (Book / WhatsApp / Call).
- All content is editable afterwards in the website builder; CTAs point at
  the existing /booking form (native website_crm).
""",
    'author': 'C2P Consultants FZC LLC',
    'license': 'OPL-1',
    'depends': ['website', 'website_crm'],
    'data': [
        'views/home_page.xml',
        'views/service_pages.xml',
    ],
    'installable': True,
    'application': False,
}
