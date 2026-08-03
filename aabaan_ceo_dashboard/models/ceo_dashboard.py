# Part of the Aabaan Odoo build by C2P Consultants FZC LLC.
from datetime import timedelta

from odoo import api, fields, models


class AabaanCeoDashboard(models.AbstractModel):
    """Data provider for the CEO dashboard client action.

    All aggregation is batched through _read_group. The x_* fields of this
    database are manual (Studio-style) fields, so every use is guarded: a
    missing field yields an empty section instead of an error, and the
    dashboard stays installable on a bare database.
    """
    _name = 'aabaan.ceo.dashboard'
    _description = 'Aaban CEO Dashboard data provider'

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    @api.model
    def _selection_labels(self, model, fname):
        info = self.env[model].fields_get([fname], ['selection']).get(fname) or {}
        return dict(info.get('selection') or [])

    @api.model
    def _sums(self, model, domain, aggregates):
        rows = self.env[model]._read_group(domain, [], aggregates)
        row = rows[0] if rows else tuple(None for _a in aggregates)
        return [value or 0 for value in row]

    @api.model
    def _group_amounts(self, model, base_domain, fname):
        """Gross/count grouped by a (possibly manual) selection field."""
        Model = self.env[model]
        if fname not in Model._fields:
            return []
        labels = self._selection_labels(model, fname)
        out = []
        for value, total, count in Model._read_group(
                base_domain, [fname], ['amount_total:sum', '__count']):
            out.append({
                'key': str(value or 'none'),
                'label': labels.get(value, value or 'Not set'),
                'gross': total or 0.0,
                'count': count,
                'model': model,
                'domain': base_domain + [(fname, '=', value)],
            })
        out.sort(key=lambda item: -item['gross'])
        return out

    # ------------------------------------------------------------------
    # payload
    # ------------------------------------------------------------------

    @api.model
    def get_data(self):
        env = self.env
        company = env.company
        today = fields.Date.context_today(self)
        now = fields.Datetime.now()
        today_s = fields.Date.to_string(today)

        Sale = env['sale.order']
        book_domain = [('state', '=', 'sale')]
        gross, net, count = self._sums(
            'sale.order', book_domain,
            ['amount_total:sum', 'amount_untaxed:sum', '__count'])

        data = {
            'company': company.name,
            'currency': company.currency_id.symbol or company.currency_id.name or 'AED',
            'as_of': fields.Datetime.to_string(now),
            'book': {
                'label': 'Confirmed contracts',
                'gross': gross, 'net': net, 'count': count,
                'model': 'sale.order', 'domain': book_domain,
            },
            'quotes': {},
            'service_lines': self._group_amounts('sale.order', book_domain, 'x_service_line'),
            'emirates': self._group_amounts('sale.order', book_domain, 'x_emirate_regime'),
            'renewals': [],
            'visits': {'by_type': [], 'cards': []},
            'pipeline': {},
            'ar': {},
            'customers': {},
        }

        q_domain = [('state', 'in', ('draft', 'sent'))]
        q_gross, q_count = self._sums('sale.order', q_domain, ['amount_total:sum', '__count'])
        data['quotes'] = {'label': 'Open quotations', 'gross': q_gross, 'count': q_count,
                          'model': 'sale.order', 'domain': q_domain}

        # renewals — sale_subscription's end_date
        if 'end_date' in Sale._fields:
            in90_s = fields.Date.to_string(today + timedelta(days=90))

            def bucket(key, label, extra, status=None):
                domain = book_domain + extra
                total, cnt = self._sums('sale.order', domain, ['amount_total:sum', '__count'])
                data['renewals'].append({
                    'key': key, 'label': label, 'gross': total, 'count': cnt,
                    'status': status, 'model': 'sale.order', 'domain': domain,
                })

            bucket('past', 'Past end-of-term',
                   [('end_date', '!=', False), ('end_date', '<', today_s)], 'critical')
            bucket('next90', 'Next 90 days',
                   [('end_date', '>=', today_s), ('end_date', '<=', in90_s)], 'warning')
            bucket('later', 'Beyond 90 days', [('end_date', '>', in90_s)])
            bucket('open_ended', 'No end date set', [('end_date', '=', False)])

        # field service visits
        Task = env['project.task']
        fsm_domain = [('project_id.is_fsm', '=', True)]
        if 'x_visit_type' in Task._fields:
            labels = self._selection_labels('project.task', 'x_visit_type')
            for value, cnt in Task._read_group(fsm_domain, ['x_visit_type'], ['__count']):
                data['visits']['by_type'].append({
                    'key': str(value or 'none'),
                    'label': labels.get(value, value or 'Untyped'),
                    'count': cnt, 'model': 'project.task',
                    'domain': fsm_domain + [('x_visit_type', '=', value)],
                })
        open_domain = fsm_domain + [('stage_id.fold', '=', False)]
        now_s = fields.Datetime.to_string(now)

        def vcard(key, label, domain, status=None):
            data['visits']['cards'].append({
                'key': key, 'label': label, 'count': Task.search_count(domain),
                'status': status, 'model': 'project.task', 'domain': domain,
            })

        if 'planned_date_begin' in Task._fields:
            in30_s = fields.Datetime.to_string(now + timedelta(days=30))
            vcard('next30', 'Visits scheduled, next 30 days',
                  open_domain + [('planned_date_begin', '>=', now_s),
                                 ('planned_date_begin', '<=', in30_s)])
            vcard('overdue', 'Past planned date, still open',
                  open_domain + [('planned_date_begin', '<', now_s)], 'critical')
        if 'x_sla_due' in Task._fields:
            vcard('sla_breach', 'SLA deadline passed, still open',
                  open_domain + [('x_sla_due', '<', now_s)], 'critical')

        # CRM pipeline (active, not won)
        if 'crm.lead' in env:
            lead_domain = ['|', ('stage_id', '=', False), ('stage_id.is_won', '=', False)]
            expected, lead_count = self._sums(
                'crm.lead', lead_domain, ['expected_revenue:sum', '__count'])
            data['pipeline'] = {'label': 'Open pipeline', 'expected': expected,
                                'count': lead_count, 'model': 'crm.lead',
                                'domain': lead_domain}

        # receivables (posted customer invoices, not fully paid)
        ar_domain = [('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),
                     ('payment_state', 'in', ('not_paid', 'partial'))]
        residual, ar_count = self._sums(
            'account.move', ar_domain, ['amount_residual:sum', '__count'])
        overdue_domain = ar_domain + [('invoice_date_due', '<', today_s)]
        overdue, overdue_count = self._sums(
            'account.move', overdue_domain, ['amount_residual:sum', '__count'])
        data['ar'] = {
            'label': 'Receivables outstanding', 'residual': residual, 'count': ar_count,
            'overdue': overdue, 'overdue_count': overdue_count,
            'model': 'account.move', 'domain': ar_domain, 'overdue_domain': overdue_domain,
        }

        data['customers'] = {
            'label': 'Customers', 'count': env['res.partner'].search_count(
                [('customer_rank', '>', 0)]),
            'model': 'res.partner', 'domain': [('customer_rank', '>', 0)],
        }
        return data
