# Part of the Aabaan Odoo build by C2P Consultants FZC LLC.
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Finance requirements §4.1: everything outstanding up to 31 Jul 2026 is
# "Previous Recovery" — the company-history cutoff, never mixed with current.
RECOVERY_CUTOFF = date(2026, 8, 1)


class AccountMove(models.Model):
    _inherit = 'account.move'

    recovery_bucket = fields.Selection([
        ('previous', 'Previous Recovery'),
        ('current', 'Current Recovery'),
        ('future', 'Future Due'),
    ], compute='_compute_recovery_bucket', store=True,
        help="Previous: due before 1 Aug 2026 (company-history cutoff). "
             "Current: due this calendar month. Future: due later. "
             "Refreshed daily.")
    recovery_status = fields.Selection([
        ('under_recovery', 'Under Recovery'),
        ('payment_promised', 'Payment Promised'),
    ], string="Recovery Status", copy=False, tracking=True,
        help="Manual collection status; Partially/Fully Paid and Overdue "
             "come from the payment state and due date.")
    recovery_promise_date = fields.Date(string="Promised Date", copy=False)
    aabaan_services = fields.Char(
        string="Services", store=True, compute='_compute_aabaan_services',
        help="All services on the contracts behind this invoice — the "
             "service dimension of the recovery grid (§5).")

    @api.depends('invoice_line_ids.sale_line_ids')
    def _compute_aabaan_services(self):
        line_has_sale = 'sale_line_ids' in self.env['account.move.line']._fields
        for move in self:
            names = []
            if line_has_sale and move.move_type in ('out_invoice', 'out_refund'):
                for order in move.invoice_line_ids.sale_line_ids.order_id:
                    if not hasattr(order, 'aabaan_service_names'):
                        break
                    for name in order.aabaan_service_names():
                        if name not in names:
                            names.append(name)
            move.aabaan_services = " + ".join(names)

    @api.depends('invoice_date_due', 'move_type', 'state', 'payment_state')
    def _compute_recovery_bucket(self):
        today = fields.Date.context_today(self)
        month_start = today.replace(day=1)
        month_end = month_start + relativedelta(months=1, days=-1)
        for move in self:
            bucket = False
            if (move.move_type == 'out_invoice' and move.state == 'posted'
                    and move.payment_state in ('not_paid', 'partial')):
                due = move.invoice_date_due or move.invoice_date or today
                if due < RECOVERY_CUTOFF and due < month_start:
                    bucket = 'previous'
                elif due <= month_end:
                    bucket = 'current'
                else:
                    bucket = 'future'
            move.recovery_bucket = bucket

    @api.model
    def _cron_refresh_recovery_buckets(self):
        """Month boundaries move the buckets — recompute open invoices daily."""
        moves = self.search([
            ('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),
            ('payment_state', 'in', ('not_paid', 'partial'))])
        self.env.add_to_compute(self._fields['recovery_bucket'], moves)

    # ------------------------------------------------------------------
    # Priority 1 — enforced branch/service analytic segregation
    # ------------------------------------------------------------------

    @api.model
    def _aabaan_analytic_plans(self):
        Plan = self.env['account.analytic.plan']
        emirate = Plan.search([('name', 'ilike', 'emirate')], limit=1)
        service = Plan.search([('name', 'ilike', 'service')], limit=1)
        return emirate, service

    def _aabaan_find_analytic_account(self, plan, needle):
        if not (plan and needle):
            return self.env['account.analytic.account']
        needle = str(needle).replace('_', ' ').casefold()
        for account in self.env['account.analytic.account'].search(
                [('root_plan_id', '=', plan.id)]):
            name = (account.name or '').casefold()
            if needle in name or name in needle:
                return account
        return self.env['account.analytic.account']

    def _aabaan_autofill_analytic(self, emirate_plan, service_plan):
        """Fill missing tags from the source contract before enforcing."""
        for move in self:
            for line in move.invoice_line_ids.filtered(
                    lambda l: l.display_type == 'product'):
                order = line.sale_line_ids.order_id[:1] if 'sale_line_ids' in line._fields else False
                if not order:
                    continue
                dist = dict(line.analytic_distribution or {})
                plans = self._aabaan_line_plans(dist)
                add = self.env['account.analytic.account']
                if emirate_plan and emirate_plan.id not in plans:
                    label = order._aabaan_selection_display('x_emirate_regime') \
                        if hasattr(order, '_aabaan_selection_display') else order._xval('x_emirate_regime')
                    add |= self._aabaan_find_analytic_account(emirate_plan, label)
                if service_plan and service_plan.id not in plans:
                    label = order._aabaan_selection_display('x_service_line') \
                        if hasattr(order, '_aabaan_selection_display') else order._xval('x_service_line')
                    add |= self._aabaan_find_analytic_account(service_plan, label)
                if add:
                    for account in add:
                        dist[str(account.id)] = 100
                    line.analytic_distribution = dist

    def _aabaan_line_plans(self, dist):
        ids = set()
        for key in (dist or {}):
            for part in str(key).split(','):
                if part.strip().isdigit():
                    ids.add(int(part))
        accounts = self.env['account.analytic.account'].browse(list(ids)).exists()
        return set(accounts.mapped('root_plan_id').ids)

    def _aabaan_check_analytic_segregation(self):
        if self.env.context.get('aabaan_skip_analytic_check'):
            return
        if self.env['ir.config_parameter'].sudo().get_param(
                'aabaan_finance_core.enforce_analytic', '1') != '1':
            return
        emirate_plan, service_plan = self._aabaan_analytic_plans()
        if not emirate_plan and not service_plan:
            return  # plans not configured on this database — nothing to enforce
        invoices = self.filtered(lambda m: m.move_type in (
            'out_invoice', 'out_refund', 'in_invoice', 'in_refund'))
        invoices._aabaan_autofill_analytic(emirate_plan, service_plan)

        def check(move, line, required_plans):
            plans = self._aabaan_line_plans(line.analytic_distribution)
            missing = [plan.name for plan in required_plans
                       if plan and plan.id not in plans]
            if missing:
                raise UserError(_(
                    "%(move)s cannot be posted: line \"%(line)s\" has no "
                    "%(missing)s analytic tag.\n\nEvery financial transaction "
                    "must be traceable through the branch (Finance policy "
                    "§7/§20). Set the analytic distribution on the line, "
                    "then post.",
                    move=move.display_name,
                    line=(line.name or line.product_id.display_name or '?'),
                    missing=" and ".join(missing)))

        for move in invoices:
            # Customer invoices: branch AND service. Vendor bills: branch only
            # (overheads like utilities have no service line — §7 requires
            # Branch → Department → Expense Category, not a service).
            required = [emirate_plan, service_plan] \
                if move.move_type in ('out_invoice', 'out_refund') \
                else [emirate_plan]
            for line in move.invoice_line_ids.filtered(
                    lambda l: l.display_type == 'product'):
                check(move, line, required)

        # Manual journal entries hitting expense accounts need the branch too.
        for move in self.filtered(lambda m: m.move_type == 'entry'):
            for line in move.line_ids.filtered(
                    lambda l: l.account_id.account_type
                    and l.account_id.account_type.startswith('expense')):
                check(move, line, [emirate_plan])

    def _post(self, soft=True):
        self._aabaan_check_analytic_segregation()
        return super()._post(soft=soft)
