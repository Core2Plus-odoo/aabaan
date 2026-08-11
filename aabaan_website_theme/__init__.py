def _post_init_hook(env):
    """Make the booking-first page the live homepage — the same mechanism as
    the builder's "Use as homepage" (website.homepage_url), reversible in
    Website settings at any time."""
    Website = env['website']
    if 'homepage_url' in Website._fields:
        Website.search([]).write({'homepage_url': '/home-v2'})
