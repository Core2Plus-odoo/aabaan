# Part of the Aabaan Odoo build by C2P Consultants FZC LLC.
from datetime import timedelta

from dateutil.relativedelta import relativedelta

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
            'industries': [],
            'size_bands': [],
            'renewals': [],
            'renewal_months': [],
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

            # month-by-month renewal timeline: everything before this month is
            # "overdue"; then the next 12 calendar months; then one tail bucket.
            month_start = today.replace(day=1)
            horizon = month_start + relativedelta(months=12)
            past_domain = book_domain + [('end_date', '!=', False),
                                         ('end_date', '<', fields.Date.to_string(month_start))]
            p_total, p_cnt = self._sums('sale.order', past_domain,
                                        ['amount_total:sum', '__count'])
            data['renewal_months'].append({
                'key': 'past', 'label': 'Overdue', 'gross': p_total, 'count': p_cnt,
                'status': 'critical', 'model': 'sale.order', 'domain': past_domain,
            })
            for offset in range(12):
                m_from = month_start + relativedelta(months=offset)
                m_to = month_start + relativedelta(months=offset + 1)
                m_domain = book_domain + [
                    ('end_date', '>=', fields.Date.to_string(m_from)),
                    ('end_date', '<', fields.Date.to_string(m_to))]
                m_total, m_cnt = self._sums('sale.order', m_domain,
                                            ['amount_total:sum', '__count'])
                data['renewal_months'].append({
                    'key': m_from.strftime('%Y-%m'), 'label': m_from.strftime('%b'),
                    'gross': m_total, 'count': m_cnt,
                    'model': 'sale.order', 'domain': m_domain,
                })
            tail_domain = book_domain + [('end_date', '>=', fields.Date.to_string(horizon))]
            t_total, t_cnt = self._sums('sale.order', tail_domain,
                                        ['amount_total:sum', '__count'])
            data['renewal_months'].append({
                'key': 'beyond', 'label': 'Later', 'gross': t_total, 'count': t_cnt,
                'model': 'sale.order', 'domain': tail_domain,
            })

        # book by client industry (res.partner.industry_id)
        industry_map = {}
        for partner, total, count in Sale._read_group(
                book_domain, ['partner_id'], ['amount_total:sum', '__count']):
            industry = partner.industry_id
            entry = industry_map.setdefault(industry.id or 0, {
                'key': str(industry.id or 'none'),
                'label': industry.name or 'Industry not set',
                'gross': 0.0, 'count': 0, 'partners': 0,
                'model': 'sale.order',
                'domain': book_domain + [
                    ('partner_id.industry_id', '=', industry.id or False)],
            })
            entry['gross'] += total or 0.0
            entry['count'] += count
            entry['partners'] += 1
        data['industries'] = sorted(
            industry_map.values(), key=lambda item: -item['gross'])

        # contract size mix
        for key, label, extra in (
                ('lt500', 'Below 500', [('amount_total', '<', 500)]),
                ('b500', '500 – 999',
                 [('amount_total', '>=', 500), ('amount_total', '<', 1000)]),
                ('b1k', '1,000 – 4,999',
                 [('amount_total', '>=', 1000), ('amount_total', '<', 5000)]),
                ('b5k', '5,000 – 19,999',
                 [('amount_total', '>=', 5000), ('amount_total', '<', 20000)]),
                ('b20k', '20,000 and above', [('amount_total', '>=', 20000)])):
            domain = book_domain + extra
            b_total, b_cnt = self._sums('sale.order', domain,
                                        ['amount_total:sum', '__count'])
            data['size_bands'].append({
                'key': key, 'label': label, 'gross': b_total, 'count': b_cnt,
                'model': 'sale.order', 'domain': domain,
            })

        # Dubai LO 11 F&B premises flag (from aabaan_visit_schedule)
        if 'is_fnb_premises' in Sale._fields:
            fnb_domain = book_domain + [('is_fnb_premises', '=', True)]
            data['fnb'] = {
                'label': 'F&B premises (Dubai LO 11)',
                'count': Sale.search_count(fnb_domain),
                'model': 'sale.order', 'domain': fnb_domain,
            }

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

        # revenue trend — posted customer invoices net of VAT, by month
        inv_base = [('move_type', 'in', ('out_invoice', 'out_refund')),
                    ('state', '=', 'posted')]
        trend_start = today.replace(day=1)
        data['revenue_months'] = []
        for offset in range(-11, 1):
            m_from = trend_start + relativedelta(months=offset)
            m_to = trend_start + relativedelta(months=offset + 1)
            m_domain = inv_base + [
                ('invoice_date', '>=', fields.Date.to_string(m_from)),
                ('invoice_date', '<', fields.Date.to_string(m_to))]
            m_total, m_cnt = self._sums(
                'account.move', m_domain,
                ['amount_untaxed_signed:sum', '__count'])
            data['revenue_months'].append({
                'key': m_from.strftime('%Y-%m'),
                'label': m_from.strftime('%b'),
                'gross': m_total, 'count': m_cnt,
                'model': 'account.move', 'domain': m_domain,
            })

        # cash collected — inbound posted payments, by month
        def collected(start, end):
            domain = [
                ('payment_type', '=', 'inbound'),
                ('state', 'in', ('posted', 'paid', 'in_process')),
                ('date', '>=', fields.Date.to_string(start)),
                ('date', '<', fields.Date.to_string(end))]
            amount, count = self._sums(
                'account.payment', domain, ['amount:sum', '__count'])
            return {'label': 'Cash collected', 'gross': amount, 'count': count,
                    'model': 'account.payment', 'domain': domain}

        data['collections_months'] = []
        for offset in range(-11, 1):
            m_from = trend_start + relativedelta(months=offset)
            m_to = trend_start + relativedelta(months=offset + 1)
            entry = collected(m_from, m_to)
            entry.update(key=m_from.strftime('%Y-%m'),
                         label=m_from.strftime('%b'))
            data['collections_months'].append(entry)

        # this month vs last month — both real sums shown side by side
        def period_metrics(offset):
            start = trend_start + relativedelta(months=offset)
            end = start + relativedelta(months=1)
            s, e = fields.Date.to_string(start), fields.Date.to_string(end)
            out = {}
            nb_domain = [('state', '=', 'sale'),
                         ('date_order', '>=', s), ('date_order', '<', e)]
            g, c = self._sums('sale.order', nb_domain,
                              ['amount_total:sum', '__count'])
            out['new_book'] = {'label': 'New contracts', 'gross': g, 'count': c,
                               'model': 'sale.order', 'domain': nb_domain}
            iv_domain = inv_base + [('invoice_date', '>=', s),
                                    ('invoice_date', '<', e)]
            g, c = self._sums('account.move', iv_domain,
                              ['amount_untaxed_signed:sum', '__count'])
            out['invoiced'] = {'label': 'Invoiced (net)', 'gross': g, 'count': c,
                               'model': 'account.move', 'domain': iv_domain}
            out['collected'] = collected(start, end)
            if 'crm.lead' in env:
                l_domain = [('create_date', '>=', s), ('create_date', '<', e)]
                out['leads'] = {'label': 'New leads',
                                'count': env['crm.lead'].search_count(l_domain),
                                'model': 'crm.lead', 'domain': l_domain}
            return out

        data['this_month'] = period_metrics(0)
        data['last_month'] = period_metrics(-1)

        # top customers — concentration of the confirmed book
        data['top_customers'] = []
        rows = Sale._read_group(
            book_domain, ['partner_id'], ['amount_total:sum', '__count'])
        rows.sort(key=lambda row: -(row[1] or 0.0))
        for partner, total, cnt in rows[:8]:
            data['top_customers'].append({
                'key': str(partner.id), 'label': partner.name,
                'gross': total or 0.0, 'count': cnt,
                'share': round(100.0 * (total or 0.0) / gross, 1) if gross else 0.0,
                'model': 'sale.order',
                'domain': book_domain + [('partner_id', '=', partner.id)],
            })

        # top technicians — completed visits (field ops stamps completion)
        data['technicians'] = []
        done_domain = fsm_domain + (
            [('visit_completed_at', '!=', False)]
            if 'visit_completed_at' in Task._fields
            else [('stage_id.fold', '=', True)])
        for user, cnt in Task._read_group(done_domain, ['user_ids'], ['__count']):
            if not user:
                continue
            data['technicians'].append({
                'key': str(user.id), 'label': user.name, 'count': cnt,
                'open': Task.search_count(
                    open_domain + [('user_ids', 'in', user.id)]),
                'model': 'project.task',
                'domain': done_domain + [('user_ids', 'in', user.id)],
            })
        data['technicians'].sort(key=lambda item: -item['count'])
        data['technicians'] = data['technicians'][:8]

        # visit workload by emirate (through the contract's emirate regime)
        data['visit_emirates'] = []
        if 'x_emirate_regime' in Sale._fields and 'sale_order_id' in Task._fields:
            labels = self._selection_labels('sale.order', 'x_emirate_regime')
            for value, label in labels.items():
                domain = fsm_domain + [
                    ('sale_order_id.x_emirate_regime', '=', value)]
                cnt = Task.search_count(domain)
                if not cnt:
                    continue
                data['visit_emirates'].append({
                    'key': str(value), 'label': label, 'count': cnt,
                    'open': Task.search_count(
                        open_domain
                        + [('sale_order_id.x_emirate_regime', '=', value)]),
                    'model': 'project.task', 'domain': domain,
                })
            data['visit_emirates'].sort(key=lambda item: -item['count'])
        return data
