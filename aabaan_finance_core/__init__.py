from . import models


def _post_init_hook(env):
    """§7: expenses run Company → Branch → Department → Category. The Emirate
    and Service Line plans exist from Phase 0; ensure a Department plan exists
    for finance to fill with its departments (data-only, no accounts seeded)."""
    Plan = env['account.analytic.plan']
    if not Plan.search([('name', 'ilike', 'department')], limit=1):
        Plan.create({'name': 'Department'})

    # Standard-first: configure NATIVE analytic applicability so the policy
    # lives where accountants expect it (Accounting > Configuration >
    # Analytic Plans), mirroring the enforcement matrix: Emirate mandatory on
    # invoices and bills, Service Line mandatory on invoices only. The custom
    # _post check remains only for what native cannot do — auto-filling tags
    # from the contract and one clear message — and can be switched off via
    # aabaan_finance_core.enforce_analytic once native applicability alone is
    # preferred. Best-effort: skipped silently if the applicability model
    # differs on this build.
    try:
        Applicability = env['account.analytic.applicability']
        emirate = Plan.search([('name', 'ilike', 'emirate')], limit=1)
        service = Plan.search([('name', 'ilike', 'service')], limit=1)
        wanted = []
        if emirate:
            wanted += [(emirate, 'invoice'), (emirate, 'bill')]
        if service:
            wanted += [(service, 'invoice')]
        domains = dict(Applicability._fields['business_domain'].selection)
        for plan, domain in wanted:
            if domain not in domains:
                continue
            if not Applicability.search([
                    ('analytic_plan_id', '=', plan.id),
                    ('business_domain', '=', domain)], limit=1):
                Applicability.create({
                    'analytic_plan_id': plan.id,
                    'business_domain': domain,
                    'applicability': 'mandatory',
                })
    except Exception:  # noqa: BLE001 — config sugar must never break install
        pass
