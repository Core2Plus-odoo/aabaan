# Part of the Aabaan Odoo build by C2P Consultants FZC LLC.
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestClientSites(TransactionCase):

    def test_locations_and_area_flow(self):
        client = self.env['res.partner'].create({
            'name': 'Sites Test Group', 'is_company': True})
        site = self.env['res.partner'].create({
            'name': 'Sites Test Group — Tower A',
            'parent_id': client.id, 'type': 'delivery',
            'aabaan_area': 'Al Nuaimiya'})
        client.invalidate_recordset()
        self.assertEqual(client.aabaan_location_count, 1)
        action = client.action_view_locations()
        self.assertEqual(action['res_model'], 'res.partner')

        project = self.env['project.project'].create({
            'name': 'Sites Test FSM', 'is_fsm': True})
        task = self.env['project.task'].create({
            'name': 'Visit Tower A', 'project_id': project.id,
            'partner_id': site.id})
        self.assertEqual(task.aabaan_area, 'Al Nuaimiya')
        site.aabaan_area = 'Al Rashidiya 2'
        self.assertEqual(task.aabaan_area, 'Al Rashidiya 2')

        product = self.env['product.product'].create({
            'name': 'Sites AMC (test)', 'type': 'service',
            'list_price': 100.0})
        order = self.env['sale.order'].create({
            'partner_id': client.id,
            'partner_shipping_id': site.id,
            'order_line': [(0, 0, {'product_id': product.id,
                                   'product_uom_qty': 1})],
        })
        self.assertEqual(order.aabaan_site_area, 'Al Rashidiya 2')

    def test_site_address_relabel(self):
        order_fields = self.env['sale.order'].fields_get(
            ['partner_shipping_id'], ['string'])
        self.assertEqual(
            order_fields['partner_shipping_id']['string'], 'Site Address')
        move_fields = self.env['account.move'].fields_get(
            ['partner_shipping_id'], ['string'])
        if move_fields.get('partner_shipping_id'):
            self.assertEqual(
                move_fields['partner_shipping_id']['string'], 'Site Address')
