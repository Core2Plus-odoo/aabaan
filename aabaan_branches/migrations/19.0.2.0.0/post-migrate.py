from odoo import SUPERUSER_ID, api

from odoo.addons.aabaan_branches import _setup_entities, _setup_head_office


def migrate(cr, version):
    """Branches become separate legal entities per the licence documents:
    Dubai and Sharjah detach with their own licence facts, UAQ / RAK are
    archived, licence expiries seeded, letterhead registry corrected."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    _setup_head_office(env)
    _setup_entities(env)
