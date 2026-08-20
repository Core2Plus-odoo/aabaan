import logging

from . import models

_logger = logging.getLogger(__name__)

# Facts transcribed from the trade licence documents (uploaded scans):
# Ajman DED professional licence, Dubai DET professional licence,
# Sharjah EDD trading licence. No figure here is invented.
ENTITIES = [
    {
        'main': True,
        'hints': ('ajman',),
        'name': 'Aaban Classic Building Cleaning L.L.C.',
        'registry': '103074',
        'licence_expiry': '2027-01-08',
        'street': 'Shop 2, Al Nuaimiya 1',
        'city': 'Ajman',
        'state_hint': 'Ajman',
    },
    {
        'hints': ('dubai',),
        'name': 'Aaban Classic Building Cleaning — Dubai',
        'registry': '989256',
        'licence_expiry': '2026-10-13',
        'street': 'Office 126, Bin Salloum Building, Hor Al Anz, Deira',
        'city': 'Dubai',
        'state_hint': 'Dubai',
    },
    {
        'hints': ('sharjah',),
        'name': 'Aaban Classic Building Cleaning — SHJ BR 2',
        'registry': '908692',
        'licence_expiry': '2026-07-01',
        'street': 'Shop 1-2, Al Sharq Street, Al Butina',
        'city': 'Sharjah',
        'state_hint': 'Sharjah',
    },
]
# The registry number the letterhead used to carry; it appears on none of
# the licence documents, so it is treated as a known-wrong placeholder.
LEGACY_WRONG_REGISTRY = '109374'
ARCHIVE_HINTS = ('quwain', 'khaimah')


def _setup_entities(env):
    """The emirate presences are separate legal entities (per the licence
    documents), not branches: the Ajman LLC is the main company; Dubai and
    Sharjah become standalone companies carrying their own licence facts;
    the empty UAQ / RAK companies are archived (recoverable). Idempotent —
    matching by emirate hint in name/city; values set only when empty,
    known-wrong, or coming from the licence."""
    Company = env['res.company'].sudo()
    State = env['res.country.state']
    country = env.ref('base.ae', raise_if_not_found=False)
    main = env.ref('base.main_company', raise_if_not_found=False)
    everyone = Company.with_context(active_test=False).search(
        [('id', '!=', main.id if main else False)])

    def match(hints):
        candidates = [
            company for company in everyone
            if any(hint in f"{company.name} {company.city or ''}".casefold()
                   for hint in hints)]
        # a standalone match wins; a branch shell is only a fallback
        standalone = [c for c in candidates if not c.parent_id]
        return (standalone or candidates or [Company])[0]

    def retire_branch(company):
        """Odoo forbids detaching a branch ("The company hierarchy cannot
        be changed"), so an empty branch shell is archived and renamed out
        of the way instead of converted."""
        try:
            users = env['res.users'].sudo().search(
                [('company_ids', 'in', company.id)])
            users.write({'company_ids': [(3, company.id)]})
            company.write({'active': False,
                           'name': '%s (closed branch)' % company.name})
            _logger.info("Aabaan entities: retired branch shell %s",
                         company.name)
        except Exception:
            _logger.exception("Aabaan entities: could not retire branch %s",
                              company.name)

    def state_for(hint):
        if not country:
            return State
        return State.search([
            ('country_id', '=', country.id),
            ('name', 'ilike', hint.split()[0])], limit=1)

    entities = env['res.company']
    for spec in ENTITIES:
        company = main if spec.get('main') else match(spec['hints'])
        if not spec.get('main') and company and company.parent_id:
            retire_branch(company)
            company = Company
        vals = {}
        if not company:
            create_vals = {'name': spec['name']}
            if country:
                create_vals['country_id'] = country.id
            company = Company.create(create_vals)
        if not spec.get('main'):
            if company.name != spec['name']:
                vals['name'] = spec['name']
            if not company.active:
                vals['active'] = True
        if not company.company_registry \
                or company.company_registry == LEGACY_WRONG_REGISTRY:
            vals['company_registry'] = spec['registry']
        if 'aabaan_licence_expiry' in company._fields \
                and not company.aabaan_licence_expiry:
            vals['aabaan_licence_expiry'] = spec['licence_expiry']
        if not company.street:
            vals['street'] = spec['street']
        if not company.city:
            vals['city'] = spec['city']
        if country and company.country_id != country:
            vals['country_id'] = country.id
        state = state_for(spec['state_hint'])
        if state and company.state_id != state:
            vals['state_id'] = state.id
        if vals:
            try:
                company.write(vals)
            except Exception:
                _logger.exception(
                    "Aabaan entities: could not update %s", company.name)
        entities |= company
        # a detached entity needs its own UAE chart of accounts
        if not spec.get('main') and 'account.chart.template' in env:
            try:
                if not env['account.account'].sudo().with_company(
                        company).search_count([]):
                    env['account.chart.template'].try_loading(
                        'ae', company=company, install_demo=False)
            except Exception:
                _logger.info(
                    "Aabaan entities: chart for %s to be configured in "
                    "Accounting settings", company.name)

    # archive the empty UAQ / RAK companies (never delete)
    for company in everyone.filtered(
            lambda c: c.active and c not in entities
            and any(h in f"{c.name} {c.city or ''}".casefold()
                    for h in ARCHIVE_HINTS)):
        try:
            users = env['res.users'].sudo().search(
                [('company_ids', 'in', company.id)])
            users.write({'company_ids': [(3, company.id)]})
            company.write({'active': False})
            _logger.info("Aabaan entities: archived %s", company.name)
        except Exception:
            _logger.exception(
                "Aabaan entities: could not archive %s", company.name)

    if main:
        users = env['res.users'].sudo().search(
            [('company_ids', 'in', main.id)])
        users.write({'company_ids': [(4, c.id) for c in entities]})


# Odoo demo defaults that must never appear on the public contact page.
PLACEHOLDER_HINTS = ('fake', 'example.com', 'yourcompany', '555-555',
                     'my company')


def _looks_placeholder(value):
    return bool(value) and any(
        hint in value.casefold() for hint in PLACEHOLDER_HINTS)


def _setup_head_office(env):
    """Replace Odoo's demo contact data on the head office with the real
    facts (letterhead / licence documents). Only empty or clearly
    placeholder values are touched."""
    main = env.ref('base.main_company', raise_if_not_found=False)
    if not main:
        return
    vals = {}
    if not main.phone or _looks_placeholder(main.phone):
        vals['phone'] = '800 22226'
    if not main.email or _looks_placeholder(main.email):
        vals['email'] = 'infoaabanservices@gmail.com'
    if not main.website or _looks_placeholder(main.website):
        vals['website'] = 'https://core2plus-odoo-aabaan.odoo.com'
    if _looks_placeholder(main.street):
        vals['street'] = False
    if _looks_placeholder(main.street2):
        vals['street2'] = False
    if vals:
        main.write(vals)
    if not main.vat:
        try:
            main.write({'vat': '104302919600003'})
        except Exception:
            pass  # a VAT validator rejecting the format must not break install


def _setup_branches(env):
    """Kept for the 19.0.1.1.0 migration — the branch model was replaced
    by separate legal entities."""
    _setup_entities(env)


def _post_init_hook(env):
    _setup_head_office(env)
    _setup_entities(env)
