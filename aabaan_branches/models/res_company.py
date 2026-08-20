# Part of the Aabaan Odoo build by C2P Consultants FZC LLC.
from datetime import timedelta

from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    aabaan_licence_expiry = fields.Date(
        string="Trade Licence Expiry",
        help="From the licence document. A daily check raises a renewal "
             "activity 60 days before expiry (and keeps raising it while "
             "expired).")

    @api.model
    def _cron_aabaan_licence_expiry(self):
        today = fields.Date.context_today(self)
        horizon = today + timedelta(days=60)
        todo = self.env.ref('mail.mail_activity_data_todo',
                            raise_if_not_found=False)
        for company in self.search([
                ('aabaan_licence_expiry', '!=', False),
                ('aabaan_licence_expiry', '<=', horizon)]):
            partner = company.partner_id
            summary = _("Trade licence renewal — %s") % company.name
            existing = self.env['mail.activity'].search([
                ('res_model', '=', 'res.partner'),
                ('res_id', '=', partner.id),
                ('summary', '=', summary),
                ('date_deadline', '>=', today),
            ], limit=1)
            if existing:
                continue
            partner.activity_schedule(
                'mail.mail_activity_data_todo' if todo else False,
                date_deadline=min(company.aabaan_licence_expiry, horizon),
                summary=summary,
                note=_("Licence %(reg)s expires on %(date)s. Renew it and "
                       "update the expiry date on the company form.",
                       reg=company.company_registry or '-',
                       date=company.aabaan_licence_expiry),
            )
