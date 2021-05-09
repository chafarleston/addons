# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    l10n_pe_journal_id = fields.Many2one(comodel_name='account.journal', domain=[('type', '=', 'sale')],
                                         string='Diario')

    @api.multi
    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        if self.l10n_pe_journal_id:
            res.update({
                'journal_id': self.l10n_pe_journal_id.id
            })
        return res
