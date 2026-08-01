# Part of the Aabaan Odoo build by C2P Consultants FZC LLC.
from odoo import _, models
from odoo.exceptions import UserError


class ProjectTask(models.Model):
    _inherit = 'project.task'

    def _aabaan_contract(self):
        self.ensure_one()
        order = self.sale_order_id
        if not order:
            raise UserError(_(
                "%s is not linked to a contract (sale order), so a follow-up "
                "or complaint visit cannot be raised from it.")
                % self.display_name)
        return order

    def action_create_followup_visit(self):
        self.ensure_one()
        return self._aabaan_contract()._create_adhoc_visit('followup')

    def action_create_complaint_visit(self):
        self.ensure_one()
        return self._aabaan_contract()._create_adhoc_visit('complaint')
