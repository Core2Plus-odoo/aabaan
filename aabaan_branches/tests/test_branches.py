from odoo.tests import TransactionCase, tagged

from odoo.addons.aabaan_branches import BRANCH_EMIRATES, _setup_branches


@tagged('post_install', '-at_install')
class TestEmirateBranches(TransactionCase):

    def _branches(self):
        main = self.env.ref('base.main_company')
        return self.env['res.company'].search([('parent_id', '=', main.id)])

    def test_four_branches_seeded(self):
        branches = self._branches()
        for emirate in BRANCH_EMIRATES:
            match = branches.filtered(
                lambda c: emirate.casefold() in (c.name or '').casefold())
            self.assertEqual(
                len(match), 1, f"expected exactly one {emirate} branch")

    def test_seeding_is_idempotent(self):
        before = len(self._branches())
        _setup_branches(self.env)
        self.assertEqual(len(self._branches()), before)

    def test_admin_sees_the_branches(self):
        admin = self.env.ref('base.user_admin')
        for branch in self._branches():
            self.assertIn(branch, admin.company_ids)
