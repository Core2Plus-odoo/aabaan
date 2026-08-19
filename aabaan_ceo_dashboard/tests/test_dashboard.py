# Part of the Aabaan Odoo build by C2P Consultants FZC LLC.
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCeoDashboard(TransactionCase):

    def test_payload_shape_on_bare_database(self):
        """get_data must succeed and return every section even when the
        manual x_* fields are absent and the database is empty."""
        data = self.env['aabaan.ceo.dashboard'].get_data()
        for key in ('company', 'currency', 'as_of', 'book', 'quotes',
                    'service_lines', 'emirates', 'industries', 'size_bands',
                    'renewals', 'renewal_months', 'visits',
                    'pipeline', 'ar', 'customers',
                    'revenue_months', 'technicians', 'visit_emirates'):
            self.assertIn(key, data)
        self.assertEqual(len(data['size_bands']), 5)
        self.assertEqual(len(data['revenue_months']), 12)
        self.assertIsInstance(data['technicians'], list)
        self.assertIsInstance(data['visit_emirates'], list)
        self.assertIsInstance(data['book']['gross'], (int, float))
        self.assertIsInstance(data['book']['count'], int)
        self.assertIsInstance(data['service_lines'], list)
        self.assertIsInstance(data['visits']['by_type'], list)
        self.assertIsInstance(data['visits']['cards'], list)

    def test_confirmed_order_reaches_the_book(self):
        partner = self.env['res.partner'].create({'name': 'Dash Test Customer'})
        product = self.env['product.product'].create({
            'name': 'Dash Test Service', 'type': 'service', 'list_price': 100.0})
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [(0, 0, {'product_id': product.id, 'product_uom_qty': 1})],
        })
        before = self.env['aabaan.ceo.dashboard'].get_data()
        order.action_confirm()
        after = self.env['aabaan.ceo.dashboard'].get_data()
        self.assertEqual(after['book']['count'], before['book']['count'] + 1)
        self.assertGreater(after['book']['gross'], before['book']['gross'])
        self.assertGreater(after['customers']['count'], 0)
