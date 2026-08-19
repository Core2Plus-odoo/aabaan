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

# Pages that must stay published even though this module does not own them:
# the booking form the CTAs point at, the native contact page, and common
# legal pages if the site has them.
KEEP_PUBLISHED_URLS = [
    '/booking', '/contactus', '/contact',
    '/privacy', '/privacy-policy', '/terms', '/terms-of-use', '/legal',
]


def _is_external(menu):
    url = menu.url or ''
    return url.startswith(('http://', 'https://', 'mailto:', 'tel:', '#'))


def _ensure_menu(Menu, parent, website, name, url, sequence):
    menu = Menu.search([('url', '=', url), ('parent_id', '=', parent.id),
                        ('website_id', '=', website.id)], limit=1)
    if menu:
        menu.write({'name': name, 'sequence': sequence})
    else:
        menu = Menu.create({'name': name, 'url': url, 'parent_id': parent.id,
                            'sequence': sequence, 'website_id': website.id})
    return menu


def _retire_legacy_pages(env):
    """Unpublish every website page this module does not own (except the
    keep-list above). Nothing is deleted — the old pages stay in the page
    manager and can be republished with one click."""
    our_page_ids = env['ir.model.data'].search([
        ('module', '=', 'aabaan_website_theme'),
        ('model', '=', 'website.page'),
    ]).mapped('res_id')
    legacy = env['website.page'].search([
        ('id', 'not in', our_page_ids),
        ('url', 'not in', KEEP_PUBLISHED_URLS),
        ('is_published', '=', True),
    ])
    if legacy:
        legacy.write({'is_published': False})


def _apply_site_structure(env):
    """Idempotent switch-over shared by the install hook and the upgrade
    migrations. The overhauled site fully replaces the old one:

    - the booking-first page is served at `/` (any previous homepage is
      parked, unpublished, at /home-classic — recoverable, never deleted);
    - the homepage pointer is cleared;
    - the top menu becomes exactly the defined set: legacy internal items
      (old Home/Services/Coverage/About/Contact) are removed so nothing is
      duplicated — only external links (http/mailto/tel/#) are kept;
    - every legacy page is unpublished (see _retire_legacy_pages)."""
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
        ensured_ids = []
        for name, url, sequence, children in SITE_MENUS:
            parent = _ensure_menu(Menu, root, website, name, url, sequence)
            ensured_ids.append(parent.id)
            for c_name, c_url, c_seq in children:
                _ensure_menu(Menu, parent, website, c_name, c_url, c_seq)
        legacy = root.child_id.filtered(
            lambda m: m.id not in ensured_ids
            and (not m.website_id or m.website_id.id == website.id)
            and not _is_external(m))
        if legacy:
            legacy.unlink()

    _retire_legacy_pages(env)


def _post_init_hook(env):
    _apply_site_structure(env)
