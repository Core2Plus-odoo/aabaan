from . import models


def _post_init_hook(env):
    """§7: expenses run Company → Branch → Department → Category. The Emirate
    and Service Line plans exist from Phase 0; ensure a Department plan exists
    for finance to fill with its departments (data-only, no accounts seeded)."""
    Plan = env['account.analytic.plan']
    if not Plan.search([('name', 'ilike', 'department')], limit=1):
        Plan.create({'name': 'Department'})
