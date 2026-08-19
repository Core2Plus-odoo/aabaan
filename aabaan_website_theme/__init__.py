# Site structure: top menu entries (name, url, sequence, children).
SITE_MENUS = [
    ('Home', '/', 10, []),
    ('Services', '/services', 20, [
        ('All services', '/services', 1),
        ('Pest Control', '/services/pest-control', 2),
        ('Water Tank Cleaning', '/services/water-tank', 3),
        ('Anti-Termite', '/services/anti-termite', 4),
        ('Deep Cleaning', '/services/deep-cleaning', 5),
    ]),
    ('About us', '/about', 30, []),
    ('FAQ', '/faq', 40, []),
    ('Contact', '/contactus', 50, []),
    ('Book a visit', '/booking', 60, []),
]


def _ensure_menu(Menu, parent, website, name, url, sequence):
    menu = Menu.search([('url', '=', url), ('parent_id', '=', parent.id),
                        ('website_id', '=', website.id)], limit=1)
    if menu:
        menu.write({'sequence': sequence})
    else:
        menu = Menu.create({'name': name, 'url': url, 'parent_id': parent.id,
                            'sequence': sequence, 'website_id': website.id})
    return menu


def _apply_site_structure(env):
    """Idempotent switch-over shared by the install hook and the upgrade
    migration: the booking-first page becomes the page served at `/` (any
    previous homepage is parked, unpublished, at /home-classic so it stays
    recoverable), the homepage pointer is cleared, and each website's main
    menu is completed to cover the code-defined pages. Existing menu items
    are matched by URL — client-added items are never touched."""
    Page = env['website.page']
    Menu = env['website.menu']
    Website = env['website']

    home = env.ref('aabaan_website_theme.page_home_v2', raise_if_not_found=False)
    if home:
        old_homes = Page.search([('url', '=', '/'), ('id', '!=', home.id)])
        if old_homes:
            old_homes.write({'url': '/home-classic', 'is_published': False})
        if home.url != '/':
            home.write({'url': '/'})
    if 'homepage_url' in Website._fields:
        Website.search([]).write({'homepage_url': False})

    for website in Website.search([]):
        root = Menu.search([('parent_id', '=', False),
                            ('website_id', '=', website.id)], limit=1)
        if not root:
            root = env.ref('website.main_menu', raise_if_not_found=False)
        if not root:
            continue
        for name, url, sequence, children in SITE_MENUS:
            parent = _ensure_menu(Menu, root, website, name, url, sequence)
            for c_name, c_url, c_seq in children:
                _ensure_menu(Menu, parent, website, c_name, c_url, c_seq)


def _post_init_hook(env):
    _apply_site_structure(env)
