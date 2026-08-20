# Part of the Aabaan Odoo build by C2P Consultants FZC LLC.
from odoo.tests import TransactionCase, tagged

from odoo.addons.aabaan_branches import ENTITIES, _setup_entities


@tagged('post_install', '-at_install')
class TestLegalEntities(TransactionCase):

    def _company_by_registry(self, registry):
        return self.env['res.company'].sudo().with_context(
            active_test=False).search(
            [('company_registry', '=', registry)], limit=1)

    def test_three_entities_exist_with_licence_facts(self):
        for spec in ENTITIES:
            company = self._company_by_registry(spec['registry'])
            self.assertTrue(
                company, f"missing entity for licence {spec['registry']}")
            self.assertTrue(company.active)
            self.assertFalse(
                company.parent_id,
                "entities are standalone companies, not branches")
            self.assertEqual(
                str(company.aabaan_licence_expiry), spec['licence_expiry'])

    def test_setup_is_idempotent(self):
        Company = self.env['res.company'].sudo().with_context(
            active_test=False)
        before = Company.search_count([])
        _setup_entities(self.env)
        self.assertEqual(Company.search_count([]), before)

    def test_main_registry_corrected_from_legacy(self):
        main = self.env.ref('base.main_company')
        main.company_registry = '109374'
        _setup_entities(self.env)
        self.assertEqual(main.company_registry, '103074')

    def test_licence_cron_raises_activity(self):
        main = self.env.ref('base.main_company')
        main.aabaan_licence_expiry = '2026-01-01'  # long past
        self.env['res.company']._cron_aabaan_licence_expiry()
        activity = self.env['mail.activity'].search([
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', main.partner_id.id),
        ], limit=1)
        self.assertTrue(activity)
        count = self.env['mail.activity'].search_count(
            [('res_model', '=', 'res.partner'),
             ('res_id', '=', main.partner_id.id)])
        self.env['res.company']._cron_aabaan_licence_expiry()
        self.assertEqual(
            self.env['mail.activity'].search_count(
                [('res_model', '=', 'res.partner'),
                 ('res_id', '=', main.partner_id.id)]),
            count, "no duplicate renewal activities")

    def test_branch_shell_is_retired_and_replaced(self):
        Company = self.env['res.company'].sudo()
        main = self.env.ref('base.main_company')
        dubai = self._company_by_registry('989256')
        # simulate the production situation: a branch shell in the way
        dubai.with_context(active_test=False).write(
            {'company_registry': False, 'active': False,
             'name': 'gone-away', 'city': False})
        shell = Company.create({'name': 'Dubai', 'parent_id': main.id})
        _setup_entities(self.env)
        shell.invalidate_recordset()
        self.assertFalse(shell.active, "branch shell must be archived")
        replacement = self._company_by_registry('989256')
        self.assertTrue(replacement)
        self.assertTrue(replacement.active)
        self.assertFalse(replacement.parent_id)
