# Part of the Aabaan Odoo build by C2P Consultants FZC LLC.
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestContractCockpit(TransactionCase):

    def test_cockpit_computes_on_bare_contract(self):
        partner = self.env['res.partner'].create({'name': 'Cockpit Test Co'})
        product = self.env['product.product'].create({
            'name': 'Cockpit AMC (test)', 'type': 'service',
            'list_price': 100.0})
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [(0, 0, {'product_id': product.id,
                                   'product_uom_qty': 1})],
        })
        order.action_confirm()
        self.assertEqual(order.state, 'sale')
        self.assertGreaterEqual(order.cockpit_health, 0.0)
        self.assertLessEqual(order.cockpit_health, 10.0)
        self.assertTrue(order.cockpit_health_note)
        self.assertEqual(order.cockpit_invoiced, 0.0)
        self.assertIn(order.cockpit_renewal_state,
                      ('overdue', 'window', 'running', 'none'))
        self.assertIsInstance(order.cockpit_visits_total, int)

    def test_invoice_carries_the_contract_panel(self):
        partner = self.env['res.partner'].create({'name': 'Panel Test Co'})
        product = self.env['product.product'].create({
            'name': 'Panel AMC (test)', 'type': 'service',
            'invoice_policy': 'order', 'list_price': 250.0})
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [(0, 0, {'product_id': product.id,
                                   'product_uom_qty': 1})],
        })
        order.action_confirm()
        moves = order._create_invoices()
        self.assertEqual(moves.aabaan_order_id, order)
        self.assertEqual(moves.aabaan_renewal_state,
                         order.cockpit_renewal_state)
        self.assertEqual(moves.aabaan_visits_total,
                         order.cockpit_visits_total)
        self.assertTrue(moves.aabaan_health_note)
        bill = self.env['account.move'].create({'move_type': 'in_invoice'})
        self.assertFalse(bill.aabaan_order_id)
