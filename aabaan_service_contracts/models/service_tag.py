# Part of the Aabaan Odoo build by C2P Consultants FZC LLC.
from odoo import fields, models


class AabaanServiceTag(models.Model):
    _name = 'aabaan.service.tag'
    _description = "Service Tag (per-site service labels on a contract)"
    _order = 'name'

    name = fields.Char(required=True)
    color = fields.Integer(default=0)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', "A service tag with this name already exists."),
    ]
