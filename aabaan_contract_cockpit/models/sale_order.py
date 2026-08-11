# Part of the Aabaan Odoo build by C2P Consultants FZC LLC.
from odoo import api, fields, models

DONE_HINTS = ('complete', 'report issued', 'certificate')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    cockpit_visits_total = fields.Integer(
        string="Visits Planned", compute='_compute_cockpit')
    cockpit_visits_done = fields.Integer(
        string="Visits Completed", compute='_compute_cockpit')
    cockpit_visits_overdue = fields.Integer(
        string="Visits Overdue", compute='_compute_cockpit')
    cockpit_sla_escalations = fields.Integer(
        string="SLA Escalations", compute='_compute_cockpit')
    cockpit_invoiced = fields.Monetary(
        string="Invoiced", compute='_compute_cockpit',
        currency_field='currency_id')
    cockpit_paid = fields.Monetary(
        string="Paid", compute='_compute_cockpit',
        currency_field='currency_id')
    cockpit_outstanding = fields.Monetary(
        string="Outstanding", compute='_compute_cockpit',
        currency_field='currency_id')
    cockpit_days_to_end = fields.Integer(
        string="Days to End of Term", compute='_compute_cockpit',
        help="Negative means the contract is past its end date.")
    cockpit_renewal_state = fields.Selection([
        ('overdue', 'Past end of term'),
        ('window', 'Renewal window (90 days)'),
        ('running', 'Running'),
        ('none', 'No end date'),
    ], string="Renewal", compute='_compute_cockpit')
    cockpit_health = fields.Float(
        string="Health (0-10)", compute='_compute_cockpit', digits=(3, 1))
    cockpit_health_note = fields.Char(
        string="Health Basis", compute='_compute_cockpit')

    def _compute_cockpit(self):
        Task = self.env['project.task']
        today = fields.Date.context_today(self)
        now = fields.Datetime.now()
        has_planned = 'planned_date_begin' in Task._fields

        for order in self:
            # --- delivery, from the generated Field Service visits ---
            total = done = overdue = escalated = 0
            due_count = due_done = 0
            if order.id:
                tasks = Task.search([
                    ('sale_order_id', '=', order.id),
                    ('project_id.is_fsm', '=', True)])
                total = len(tasks)
                for task in tasks:
                    stage = (task.stage_id.name or '').casefold()
                    is_done = bool(task.visit_completed_at) or any(
                        hint in stage for hint in DONE_HINTS)
                    if is_done:
                        done += 1
                    if task.sla_escalated:
                        escalated += 1
                    if has_planned and task.planned_date_begin \
                            and task.planned_date_begin < now:
                        due_count += 1
                        if is_done:
                            due_done += 1
                        elif 'cancel' not in stage:
                            overdue += 1
            order.cockpit_visits_total = total
            order.cockpit_visits_done = done
            order.cockpit_visits_overdue = overdue
            order.cockpit_sla_escalations = escalated

            # --- money, from posted customer invoices ---
            invoiced = paid = outstanding = 0.0
            for move in order.invoice_ids.filtered(
                    lambda m: m.state == 'posted'
                    and m.move_type in ('out_invoice', 'out_refund')):
                sign = -1 if move.move_type == 'out_refund' else 1
                invoiced += sign * move.amount_total
                outstanding += sign * move.amount_residual
            paid = invoiced - outstanding
            order.cockpit_invoiced = invoiced
            order.cockpit_paid = paid
            order.cockpit_outstanding = outstanding

            # --- term & renewal ---
            end = order['end_date'] if 'end_date' in order._fields else False
            if end:
                days = (end - today).days
                order.cockpit_days_to_end = days
                order.cockpit_renewal_state = (
                    'overdue' if days < 0 else
                    'window' if days <= 90 else 'running')
            else:
                order.cockpit_days_to_end = 0
                order.cockpit_renewal_state = 'none'

            # --- health: only from signals that actually exist ---
            components = []
            notes = []
            if invoiced > 0:
                ratio = max(0.0, min(1.0, paid / invoiced))
                components.append(ratio)
                notes.append("payment %d%%" % round(ratio * 100))
            if due_count:
                ratio = due_done / due_count
                components.append(ratio)
                notes.append("delivery %d%%" % round(ratio * 100))
            if total:
                ratio = 1.0 - min(1.0, escalated / total)
                components.append(ratio)
                notes.append("SLA %d%%" % round(ratio * 100))
            if components:
                order.cockpit_health = round(
                    10.0 * sum(components) / len(components), 1)
                order.cockpit_health_note = "Based on " + ", ".join(notes)
            else:
                order.cockpit_health = 0.0
                order.cockpit_health_note = "No delivery or billing activity yet"
