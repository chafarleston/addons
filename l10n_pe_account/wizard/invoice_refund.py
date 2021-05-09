# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountInvoiceRefund(models.TransientModel):
    _inherit = "account.invoice.refund"

    l10n_pe_debit_note_code = fields.Selection(selection="_get_l10n_pe_debit_note_type", string=u"Código de nota de débito")
    l10n_pe_credit_note_code = fields.Selection(selection="_get_l10n_pe_credit_note_type", string=u"Código de nota de crédito")

    @api.model
    def default_get(self, fields_list):
        res = super(AccountInvoiceRefund, self).default_get(fields_list)
        invoice_obj = self.env['account.invoice'].browse(self.env.context.get('active_id'))
        if invoice_obj.journal_id.l10n_pe_document_type_id \
                and not (invoice_obj.journal_id.l10n_pe_journal_debit_id or invoice_obj.journal_id.l10n_pe_journal_credit_id):
            raise UserError('Configure diario de NC y ND en diario: {}'.format(invoice_obj.journal_id.name))
        return res

    @api.model
    def _get_l10n_pe_credit_note_type(self):
        return self.env['l10n_pe.datas'].get_selection("PE.CPE.CATALOG9")

    @api.model
    def _get_l10n_pe_debit_note_type(self):
        return self.env['l10n_pe.datas'].get_selection("PE.CPE.CATALOG10")

    @api.multi
    def invoice_refund(self):
        res = super(AccountInvoiceRefund, self).invoice_refund()
        if self.env.context.get("is_l10n_pe_debit_note", False):
            invoice_domain = res['domain']
            if invoice_domain:
                del invoice_domain[0]
                res['domain'] = invoice_domain
        return res
