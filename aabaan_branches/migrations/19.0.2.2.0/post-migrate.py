from odoo import SUPERUSER_ID, api

from odoo.addons.aabaan_branches import _setup_entities


def migrate(cr, version):
    """Re-run the entity setup with the hierarchy fix: branch shells that
    cannot be detached (Odoo forbids changing the company hierarchy) are
    archived and replaced by fresh standalone companies carrying the
    licence facts."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    _setup_entities(env)
