# The head office (main company, Ajman) stays the parent; these four
# emirate branches complete the five-emirate coverage.
BRANCH_EMIRATES = ['Sharjah', 'Dubai', 'Umm Al Quwain', 'Ras Al Khaimah']


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
    _setup_branches(env)
