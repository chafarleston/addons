# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PosConfig(models.Model):
    _inherit = 'pos.config'

    l10n_pe_pos_auto_invoice = fields.Boolean(string='POS auto factura', default=1)
    l10n_pe_invoice_journal_ids = fields.Many2many(comodel_name='account.journal', relation='pos_config_invoice_journal_rel', column1='config_id',
                                                   column2='journal_id', string='Diarios de factura', domain=[('type', '=', 'sale')],
                                                   help="Diarios contables para la creación de comprobantes")
    l10n_pe_default_partner = fields.Many2one(comodel_name='res.partner', string='Cliente por defecto', domain=[('customer', '=', True)])
    l10n_pe_set_qty_by_amount = fields.Boolean(string='Poner cantidad por monto')
    l10n_pe_cpe_url_consult = fields.Char(string='CPE URL', default='http://test.vrs-efact.com/buscar')

    @api.multi
    def open_ui(self):
        self._check_l10n_pe_journal()
        return super(PosConfig, self).open_ui()

    @api.multi
    def open_session_cb(self):
        self._check_l10n_pe_journal()
        return super(PosConfig, self).open_session_cb()

    @api.multi
    def open_existing_session_cb(self):
        self._check_l10n_pe_journal()
        return super(PosConfig, self).open_existing_session_cb()

    @api.constrains('l10n_pe_invoice_journal_ids')
    def _check_l10n_pe_journal(self):
        self.mapped('l10n_pe_invoice_journal_ids').mapped(lambda record: record._check_l10n_pe())

