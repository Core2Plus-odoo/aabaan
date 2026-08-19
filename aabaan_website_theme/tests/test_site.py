from odoo.tests import TransactionCase, tagged

from odoo.addons.aabaan_website_theme import _apply_site_structure

PAGES = [
    ('aabaan_website_theme.page_home_v2', '/'),
    ('aabaan_website_theme.page_rec_services_index', '/services'),
    ('aabaan_website_theme.page_rec_svc_pest', '/services/pest-control'),
    ('aabaan_website_theme.page_rec_svc_tank', '/services/water-tank'),
    ('aabaan_website_theme.page_rec_svc_termite', '/services/anti-termite'),
    ('aabaan_website_theme.page_rec_svc_cleaning', '/services/deep-cleaning'),
    ('aabaan_website_theme.page_rec_about', '/about'),
    ('aabaan_website_theme.page_rec_faq', '/faq'),
]


@tagged('post_install', '-at_install')
class TestWebsiteOverhaul(TransactionCase):

    def test_pages_published_at_expected_urls(self):
        for xmlid, url in PAGES:
            page = self.env.ref(xmlid)
            self.assertEqual(page.url, url)
            self.assertTrue(page.is_published)

    def test_booking_first_page_is_the_homepage(self):
        home = self.env.ref('aabaan_website_theme.page_home_v2')
        self.assertEqual(home.url, '/')
        others = self.env['website.page'].search(
            [('url', '=', '/'), ('id', '!=', home.id)])
        self.assertFalse(
            others, "any pre-existing homepage must be parked at /home-classic")
        Website = self.env['website']
        if 'homepage_url' in Website._fields:
            self.assertFalse(
                Website.search([]).filtered('homepage_url'),
                "homepage_url must be cleared so / serves the page itself")

    def test_menus_present_and_idempotent(self):
        Menu = self.env['website.menu']
        _apply_site_structure(self.env)
        counts = {
            (website.id, url): Menu.search_count(
                [('url', '=', url), ('website_id', '=', website.id)])
            for website in self.env['website'].search([])
            for url in ['/services', '/about', '/faq', '/booking', '/contactus']
        }
        for key, count in counts.items():
            self.assertGreaterEqual(count, 1, f"menu missing for {key}")
        _apply_site_structure(self.env)
        for (website_id, url), count in counts.items():
            self.assertEqual(
                Menu.search_count(
                    [('url', '=', url), ('website_id', '=', website_id)]),
                count, f"menu for {url} duplicated on re-run")
