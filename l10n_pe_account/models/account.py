# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

import re

SELECTION_STATE = [
    ('draft', 'Draft'),
    ('open', 'Open'),
    ('in_payment', 'In Payment'),
    ('paid', 'Paid'),
    ('cancel', 'Cancelled')
]


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    l10n_pe_number = fields.Char(string='Correlativo', copy=False, readonly=True)
    l10n_pe_exchange_rate = fields.Float(string='Tipo de cambio', compute='_compute_l10n_pe_exchange_rate',
                                         digits=(10, 3), help=u'Tipo de cambio a la fecha de facturacón')
    l10n_pe_invoice_origin_id = fields.Many2one(comodel_name='account.invoice', string='Documento rectificado',
                                                readonly=True)
    l10n_pe_sunat_code = fields.Char(string='Codigo sunat', related='journal_id.l10n_pe_document_type_id.code',
                                     readonly=True)
    l10n_pe_amount_text = fields.Char("Amount Text", compute="_compute_l10n_pe_amount_text")
    l10n_pe_type_sale_operation = fields.Selection(selection="_get_l10n_pe_type_sale_operation", string="Tipo de venta",
                                                   default="0101", help=u'Según catálogo sunat N° 51', copy=False)
    l10n_pe_debit_note_code = fields.Selection(selection="_get_l10n_pe_debit_note_type", reaoonly=True,
                                               string="Codigo de nota de debito", help=u'Según catálogo sunat N° 09')
    l10n_pe_credit_note_code = fields.Selection(selection="_get_l10n_pe_credit_note_type", readonly=True,
                                                string="Codigo de nota de credito", help=u'Según catálogo sunat N° 10')
    l10n_pe_ticket_state_sunat = fields.Selection(selection="_get_l10n_pe_ticket_state_sunat", default="1",
                                                  help=u'Según catálogo sunat N° 19', string="Estado de la boleta")
    l10n_pe_reason_voided = fields.Char(string=u'Motivo de cancelación', copy=False,
                                        help=u'Descripción para anular CPE')
    reference = fields.Char(string='Payment Ref.', copy=False, readonly=True, states={'draft': [('readonly', False)]},
                            help='The payment communication that will be automatically populated once'
                                 ' the invoice validation. You can also write a free communication.')

    move_id = fields.Many2one('account.move', string='Journal Entry',readonly=True, index=True, ondelete='restrict',
                              copy=False, help="Link to the automatically generated Journal Items.")
    number = fields.Char(related='move_id.name', store=True, readonly=True, copy=False)
    amount_tax_signed = fields.Monetary(string='Tax in Invoice Currency', currency_field='currency_id', readonly=True,
                                        compute='_compute_sign_taxes')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_compute_amount')
    state = fields.Selection(selection=SELECTION_STATE, string='Status', index=True, readonly=True, default='draft',
                             track_visibility='onchange', copy=False,
                             help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Invoice.\n"
                                  " * The 'Open' status is used when user creates invoice, an invoice number is generated. It stays in the open status till the user pays the invoice.\n"
                                  " * The 'In Payment' status is used when payments have been registered for the entirety of the invoice in a journal configured to post entries at bank reconciliation only, and some of them haven't been reconciled with a bank statement line yet.\n"
                                  " * The 'Paid' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled.\n"
                                  " * The 'Cancelled' status is used when user cancel invoice.")

    @api.model
    def default_get(self, fields_list):
        res = super(AccountInvoice, self).default_get(fields_list)
        res.update({
            'date_invoice': fields.Date().context_today(self)
        })
        return res

    @api.model
    def _get_l10n_pe_credit_note_type(self):
        return self.env['l10n_pe.datas'].get_selection("PE.CPE.CATALOG9")

    @api.model
    def _get_l10n_pe_debit_note_type(self):
        return self.env['l10n_pe.datas'].get_selection("PE.CPE.CATALOG10")

    @api.model
    def _get_l10n_pe_ticket_state_sunat(self):
        return self.env['l10n_pe.datas'].get_selection("PE.CPE.CATALOG19")

    @api.depends('amount_total')
    def _compute_l10n_pe_amount_text(self):
        self.mapped(lambda w: w.update({'l10n_pe_amount_text': w.currency_id.amount_to_text(w.amount_total)}))

    @api.multi
    @api.depends('date_invoice', 'currency_id')
    def _compute_l10n_pe_exchange_rate(self):
        today = fields.Date().context_today(self)
        self.mapped(lambda x: x.update({
            'l10n_pe_exchange_rate':  x.currency_id.l10n_pe_get_rate_by_date((x.l10n_pe_invoice_origin_id or x).date_invoice or today)
        }))

    def _get_currency_rate_date(self):
        return self.l10n_pe_invoice_origin_id.date_invoice or self.date or self.date_invoice

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None, description=None, journal_id=None):
        res = super(AccountInvoice, self)._prepare_refund(
            invoice, date_invoice=date_invoice, date=date, description=description, journal_id=journal_id
        )
        journal_id = res.get('journal_id')
        if journal_id and not self.env.context.get("l10n_pe_is_debit_note"):
            journal = self.env['account.journal'].browse(journal_id)
            res.update({
                'journal_id': journal.l10n_pe_journal_credit_id.id,
            })
        elif journal_id and self.env.context.get("l10n_pe_is_debit_note"):
            journal = self.env['account.journal'].browse(journal_id)
            res.update({
                'journal_id': journal.l10n_pe_journal_debit_id.id,
                'type': 'out_invoice',
                'refund_invoice_id': False,
            })
        res['l10n_pe_invoice_origin_id'] = invoice.id
        res['date_invoice'] = fields.Date().context_today(self)
        return res

    @api.model
    def _get_l10n_pe_type_sale_operation(self):
        return self.env['l10n_pe.datas'].get_selection('PE.CPE.CATALOG51')

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'tax_line_ids.amount_rounding',
                 'currency_id', 'company_id', 'date_invoice', 'type')
    def _compute_amount(self):
        round_curr = self.currency_id.round
        self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
        self.amount_tax = sum(round_curr(line.amount_total) for line in self.tax_line_ids)
        self.amount_total = self.amount_untaxed + self.amount_tax
        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
            currency_id = self.currency_id
            amount_total_company_signed = currency_id._convert(self.amount_total, self.company_id.currency_id, self.company_id, self.date_invoice or fields.Date.today())
            amount_untaxed_signed = currency_id._convert(self.amount_untaxed, self.company_id.currency_id, self.company_id, self.date_invoice or fields.Date.today())
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        if self.state == "cancel":
            self.amount_total_signed = 0.0
            self.amount_untaxed = 0.0
            self.amount_tax = 0.0
            self.amount_tax_igv = 0.0

        self.amount_untaxed_signed = amount_untaxed_signed * sign

    @api.multi
    def action_cancel(self):
        moves = self.env['account.move']
        for inv in self:
            if inv.move_id:
                moves += inv.move_id
            #unreconcile all journal items of the invoice, since the cancellation will unlink them anyway
            inv.move_id.line_ids.filtered(lambda x: x.account_id.reconcile).remove_move_reconcile()

        # First, set the invoices as cancelled and detach the move ids
        self.write({'state': 'cancel', 'move_id': False})
        if moves:
            # second, invalidate the move(s)
            moves.button_cancel()
            # delete the move this invoice was pointing to
            # Note that the corresponding move_lines and move_reconciles
            # will be automatically deleted too
            split = self.reference.split('/')
            self.number = split[0]
            moves.unlink()
        return True


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.model
    def default_get(self, fields_list):
        res = super(AccountInvoiceLine, self).default_get(fields_list)
        if self.env.context.get('type') in ['out_invoice', 'out_refund']:
            tax = self.env['account.tax'].search([('l10n_pe_tax_type_id.code', '=', '1000')], limit=1)
            res.update({'invoice_line_tax_ids': [(6, 0, tax.ids)]})
        return res


class AccountTax(models.Model):
    _inherit = 'account.tax'

    l10n_pe_tax_type_id = fields.Many2one(comodel_name='l10n_pe.datas', domain=[('table_code', '=', 'PE.CPE.CATALOG5')], string='Tipo segun sunat')
    l10n_pe_code_tax = fields.Char(related='l10n_pe_tax_type_id.code', readonly=True)
    l10n_pe_isc_type_id = fields.Many2one(comodel_name='l10n_pe.datas', domain=[('table_code', '=', 'PE.CPE.CATALOG8')], string='Tipo ISC sunat')
    l10n_pe_type_sale_id = fields.Many2one(comodel_name='l10n_pe.datas', domain=[('table_code', '=', 'PE.CPE.CATALOG11')], string='Tipo venta (boleta)')
    l10n_pe_code_affectation_id = fields.Many2one(comodel_name='l10n_pe.datas', domain=[('table_code', '=', 'PE.CPE.CATALOG7')], string='Código de afectación sunat')


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    l10n_pe_send_sunat = fields.Boolean(string='Enviar a sunat')
    l10n_pe_is_synchronous = fields.Boolean(string='Es sincrono')
    l10n_pe_is_contingency = fields.Boolean(string='Es contingencia')
    l10n_pe_document_type_id = fields.Many2one(comodel_name='l10n_pe.datas', domain=[('table_code', 'in', ['PE.CPE.CATALOG1'])],
                                               string='Tipo de documento', help=u'Según catálogo sunat N° 01')
    l10n_pe_journal_debit_id = fields.Many2one(comodel_name='account.journal', string='Nota de debito',
                                               domain=[('l10n_pe_document_type_id.code', 'in', ['08'])], help=u'Diario contable para ND')
    l10n_pe_journal_credit_id = fields.Many2one(comodel_name='account.journal', string='Nota de credito',
                                                domain=[('l10n_pe_document_type_id.code', 'in', ['07'])], help=u'Diario contable para NC')
    l10n_pe_sunat_code = fields.Char(string='Código sunat', related='l10n_pe_document_type_id.code')

    @api.multi
    def name_get(self):
        return self.mapped(lambda record: (record.id, '{} {}'.format(record.name, record.code)))

    def _check_l10n_pe(self):
        for record in self.filtered('l10n_pe_send_sunat'):
            number = record.sequence_id.get_next_char(record.sequence_number_next)
            if not re.compile('[B][A-Z0-9]{2}[0-9]-[0-9]{1,8}|[F][A-Z0-9]{2}[0-9]-[0-9]{1,8}').match(number):
                raise ValidationError('Configure correctamente la secuencia del diario contable {} {}'.format(record.name, record.code))
        return True
