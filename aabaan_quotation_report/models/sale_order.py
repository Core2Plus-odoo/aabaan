# Part of the Aabaan Odoo build by C2P Consultants FZC LLC.
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _aabaan_selection_display(self, fname):
        """Display label of a (possibly manual/Studio) field for report
        rendering. Returns '' when the field is missing or empty, so the
        report never depends on the database-defined x_* fields existing."""
        self.ensure_one()
        if fname not in self._fields:
            return ''
        value = self[fname]
        if not value:
            return ''
        field = self._fields[fname]
        if field.type == 'selection':
            selection = field.get_description(self.env).get('selection') or []
            return dict(selection).get(value, str(value))
        return str(value)

    def _aabaan_subject(self):
        """Subject line of the printed document, e.g.
        'PEST CONTROL AMC - VILLA 12, AL RASHIDIYA 2, AJMAN'."""
        self.ensure_one()
        parts = []
        # A contract can cover several services (e.g. pest control AND
        # water tank cleaning) — name all of them, dynamically.
        if hasattr(self, 'aabaan_service_names'):
            services = self.aabaan_service_names()
        else:
            single = self._aabaan_selection_display('x_service_line')
            services = [single] if single else []
        if services:
            parts.append(" + ".join(services))
        site = self._aabaan_selection_display('x_site_address')
        if site:
            parts.append(site)
        return " - ".join(part.upper() for part in parts)

    def _aabaan_numbered_lines(self):
        """Order lines with a running number for product rows; sections and
        notes keep no=None and render as full-width rows."""
        self.ensure_one()
        rows, counter = [], 0
        for line in self.order_line:
            if line.display_type:
                rows.append({'no': None, 'line': line})
            else:
                counter += 1
                rows.append({'no': counter, 'line': line})
        return rows

    def _aabaan_amount_in_words(self):
        self.ensure_one()
        try:
            return self.currency_id.amount_to_text(self.amount_total)
        except Exception:
            return ''


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _aabaan_uom_name(self):
        self.ensure_one()
        for fname in ('product_uom_id', 'product_uom'):
            if fname in self._fields and self[fname]:
                return self[fname].name
        return ''
