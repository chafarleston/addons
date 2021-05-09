# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PosOrder(models.Model):
    _inherit = "pos.order"

    l10n_pe_invoice_journal_id = fields.Many2one(comodel_name='account.journal', string='Diario contable', readonly=1)

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        if 'l10n_pe_invoice_journal_id' in ui_order:
            res['l10n_pe_invoice_journal_id'] = ui_order['l10n_pe_invoice_journal_id']
        return res

    def _prepare_invoice(self):
        res = super(PosOrder, self)._prepare_invoice()
        if self.l10n_pe_invoice_journal_id:
            res['journal_id'] = self.l10n_pe_invoice_journal_id.id
        return res

