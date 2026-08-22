# Part of the Aabaan Odoo build by C2P Consultants FZC LLC.
from odoo.addons.aabaan_ceo_dashboard.models.ceo_dashboard import PERIODS, TABS
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCeoDashboard(TransactionCase):

    def _data(self, tab='executive', period='this_month'):
        return self.env['aabaan.ceo.dashboard'].get_data(tab, period)

    def test_every_tab_loads_on_a_bare_database(self):
        """Each tab must return a usable payload even with no records and
        with the manual x_* fields absent — a missing field collapses its
        own section, it never breaks the tab."""
        for tab, _label in TABS:
            data = self._data(tab)
            self.assertEqual(data['tab'], tab)
            for key in ('company', 'currency', 'as_of', 'tabs', 'periods',
                        'period', 'period_label', 'range', 'notes'):
                self.assertIn(key, data, "%s tab is missing %s" % (tab, key))

    def test_every_period_loads_on_every_tab(self):
        for tab, _label in TABS:
            for period, _plabel in PERIODS:
                data = self._data(tab, period)
                self.assertEqual(data['period'], period)

    def test_unknown_tab_and_period_fall_back(self):
        """A stale bookmark or a hand-edited call must not raise."""
        data = self._data('does_not_exist', 'also_not_real')
        self.assertEqual(data['tab'], 'executive')
        self.assertEqual(data['period'], 'this_month')

    def test_period_bounds_previous_window_is_same_length(self):
        Dash = self.env['aabaan.ceo.dashboard']
        for period, _label in PERIODS:
            start, end, prev_start, prev_end = Dash._period_bounds(period)
            self.assertEqual(prev_end, start,
                             "%s: previous window must end where the "
                             "current one starts" % period)
            self.assertEqual(end - start, start - prev_start,
                             "%s: the two windows must be the same length "
                             "or the delta is not like-for-like" % period)

    def test_delta_is_none_without_a_baseline(self):
        """An undefined delta must stay undefined — reporting 0% or 100%
        against a zero baseline would read as a measured fact."""
        Dash = self.env['aabaan.ceo.dashboard']
        self.assertIsNone(Dash._delta(500, 0))
        self.assertIsNone(Dash._delta(0, 0))
        self.assertEqual(Dash._delta(150, 100), 50.0)
        self.assertEqual(Dash._delta(50, 100), -50.0)

    def test_pct_is_none_without_a_denominator(self):
        Dash = self.env['aabaan.ceo.dashboard']
        self.assertIsNone(Dash._pct(3, 0))
        self.assertEqual(Dash._pct(1, 4), 25.0)

    def test_executive_tiles_and_trends(self):
        data = self._data('executive')
        self.assertTrue(data['tiles'])
        self.assertEqual(len(data['revenue_months']), 12)
        self.assertEqual(len(data['collections_months']), 12)
        for entry in data['period_block']:
            for key in ('label', 'gross', 'count', 'prev_gross', 'delta'):
                self.assertIn(key, entry)

    def test_finance_ageing_bands_cover_every_open_invoice(self):
        """The five ageing bands must partition the receivables — no
        invoice counted twice, none dropped."""
        data = self._data('finance')
        self.assertEqual(len(data['ageing']), 5)
        total_in_bands = sum(band['count'] for band in data['ageing'])
        ar = self.env['account.move'].search_count(
            self.env['aabaan.ceo.dashboard']._ar_domain())
        self.assertEqual(total_in_bands, ar)

    def test_confirmed_order_reaches_the_book(self):
        partner = self.env['res.partner'].create({'name': 'Dash Test Customer'})
        product = self.env['product.product'].create({
            'name': 'Dash Test Service', 'type': 'service', 'list_price': 100.0})
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [(0, 0, {'product_id': product.id,
                                   'product_uom_qty': 1})],
        })
        before = self._data('executive')['tiles'][0]
        order.action_confirm()
        after = self._data('executive')['tiles'][0]
        self.assertEqual(after['count'], before['count'] + 1)
        self.assertGreater(after['gross'], before['gross'])

    def test_every_drillable_figure_carries_a_real_domain(self):
        """Every tile/bar on screen claims to be one click from its
        evidence — so anything with a model must also carry a domain."""
        for tab, _label in TABS:
            data = self._data(tab)
            for key, value in data.items():
                if not isinstance(value, list):
                    continue
                for entry in value:
                    if isinstance(entry, dict) and entry.get('model'):
                        self.assertIn(
                            'domain', entry,
                            "%s → %s: drillable entry has no domain" % (tab, key))

    def test_amc_at_risk_entries_explain_themselves(self):
        """A contract only appears in the at-risk list with a stated,
        evidence-backed reason — never an unexplained score."""
        for entry in self._data('amc')['at_risk']:
            self.assertTrue(entry['reason'])
            self.assertTrue(entry['overdue'] or entry['escalated'])
