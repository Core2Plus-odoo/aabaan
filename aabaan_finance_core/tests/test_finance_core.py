# Part of the Aabaan Odoo build by C2P Consultants FZC LLC.
from freezegun import freeze_time

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestFinanceCore(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Plan = cls.env['account.analytic.plan']
        cls.emirate_plan = Plan.search([('name', 'ilike', 'emirate')], limit=1) \
            or Plan.create({'name': 'Emirate'})
        cls.service_plan = Plan.search([('name', 'ilike', 'service')], limit=1) \
            or Plan.create({'name': 'Service Line'})
        Acc = cls.env['account.analytic.account']
        cls.aa_ajman = Acc.search([('root_plan_id', '=', cls.emirate_plan.id),
                                   ('name', 'ilike', 'ajman')], limit=1) \
            or Acc.create({'name': 'Ajman', 'plan_id': cls.emirate_plan.id})
        cls.aa_pest = Acc.search([('root_plan_id', '=', cls.service_plan.id),
                                  ('name', 'ilike', 'pest')], limit=1) \
            or Acc.create({'name': 'Pest Control', 'plan_id': cls.service_plan.id})
        cls.partner = cls.env['res.partner'].create({'name': 'Recovery Test Co'})

    def _invoice(self, due, tagged_line=True, post_ctx=None):
        dist = {}
        if tagged_line:
            dist = {str(self.aa_ajman.id): 100, str(self.aa_pest.id): 100}
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_date': '2026-08-05',
            'invoice_date_due': due,
            'invoice_line_ids': [(0, 0, {
                'name': 'AMC instalment', 'quantity': 1, 'price_unit': 1000,
                'analytic_distribution': dist or False,
            })],
        })
        move.with_context(**(post_ctx or {})).action_post()
        return move

    @freeze_time('2026-08-10')
    def test_recovery_buckets(self):
        prev = self._invoice('2026-07-15')
        curr = self._invoice('2026-08-20')
        futu = self._invoice('2026-10-01')
        self.assertEqual(prev.recovery_bucket, 'previous')
        self.assertEqual(curr.recovery_bucket, 'current')
        self.assertEqual(futu.recovery_bucket, 'future')
        self.env['account.move']._cron_refresh_recovery_buckets()

    @freeze_time('2026-08-10')
    def test_analytic_enforcement(self):
        with self.assertRaises(UserError,
                               msg="untagged invoice line must not post"):
            self._invoice('2026-08-20', tagged_line=False)
        ok = self._invoice('2026-08-20', tagged_line=True)
        self.assertEqual(ok.state, 'posted')
        bypass = self._invoice('2026-08-25', tagged_line=False,
                               post_ctx={'aabaan_skip_analytic_check': True})
        self.assertEqual(bypass.state, 'posted')

    @freeze_time('2026-08-10')
    def test_vendor_bill_requires_branch_only(self):
        def bill(dist):
            move = self.env['account.move'].create({
                'move_type': 'in_invoice',
                'partner_id': self.partner.id,
                'invoice_date': '2026-08-05',
                'invoice_line_ids': [(0, 0, {
                    'name': 'Office utilities', 'quantity': 1,
                    'price_unit': 500,
                    'analytic_distribution': dist or False,
                })],
            })
            move.action_post()
            return move
        with self.assertRaises(UserError,
                               msg="untagged bill must not post"):
            bill({})
        ok = bill({str(self.aa_ajman.id): 100})  # branch alone is enough
        self.assertEqual(ok.state, 'posted')

    def test_department_plan_seeded(self):
        self.assertTrue(self.env['account.analytic.plan'].search(
            [('name', 'ilike', 'department')], limit=1))
