# The head office (main company, Ajman) stays the parent; these four
# emirate branches complete the five-emirate coverage.
BRANCH_EMIRATES = ['Sharjah', 'Dubai', 'Umm Al Quwain', 'Ras Al Khaimah']

# Odoo demo defaults that must never appear on the public contact page.
PLACEHOLDER_HINTS = ('fake', 'example.com', 'yourcompany', '555-555',
                     'my company')


def _looks_placeholder(value):
    return bool(value) and any(
        hint in value.casefold() for hint in PLACEHOLDER_HINTS)


def _setup_head_office(env):
    """Replace Odoo's demo contact data on the head office with the real
    facts (from the letterhead / trade licence). Only empty or clearly
    placeholder values are touched — real data entered by the business is
    never overwritten."""
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
    if not main.city or _looks_placeholder(main.city):
        vals['city'] = 'Ajman'
    country = env.ref('base.ae', raise_if_not_found=False)
    if country and main.country_id != country:
        vals['country_id'] = country.id
        state = env['res.country.state'].search([
            ('country_id', '=', country.id), ('name', 'ilike', 'Ajman'),
        ], limit=1)
        vals['state_id'] = state.id if state else False
        vals['zip'] = False
    if vals:
        main.write(vals)
    if not main.vat:
        try:
            main.write({'vat': '104302919600003'})
        except Exception:
            pass  # a VAT validator rejecting the format must not break install


def _setup_branches(env):
    """Idempotently seed the four emirate branches as native Odoo company
    branches (child companies of the head office — shared chart of
    accounts, taxes and fiscal settings), and let every user who can see
    the head office also see its branches."""
    main = env.ref('base.main_company', raise_if_not_found=False)
    if not main:
        return
    Company = env['res.company']
    State = env['res.country.state']
    country = main.country_id or env.ref('base.ae', raise_if_not_found=False)

    branches = Company.browse()
    existing = Company.search([('parent_id', '=', main.id)])
    for emirate in BRANCH_EMIRATES:
        branch = existing.filtered(
            lambda c: emirate.casefold() in (c.name or '').casefold())[:1]
        if not branch:
            vals = {
                'name': f"{main.name} — {emirate}",
                'parent_id': main.id,
                'city': emirate,
            }
            if country:
                vals['country_id'] = country.id
                state = State.search([
                    ('country_id', '=', country.id),
                    ('name', 'ilike', emirate.split()[0]),
                ], limit=1)
                if state:
                    vals['state_id'] = state.id
            branch = Company.create(vals)
        branches |= branch

    if branches:
        users = env['res.users'].search([('company_ids', 'in', main.id)])
        users.write({'company_ids': [(4, b.id) for b in branches]})


def _post_init_hook(env):
    _setup_head_office(env)
    _setup_branches(env)
