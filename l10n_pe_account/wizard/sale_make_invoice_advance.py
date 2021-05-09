# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.multi
    def create_invoices(self):
        res = super(SaleAdvancePaymentInv, self).create_invoices()
        order = self.env['sale.order'].browse(self._context.get('active_ids', []))
        for invoice_id in order.invoice_ids:
            journal_id = False
            if invoice_id.partner_id.doc_type=="6" and invoice_id.state=='draft':
                journal=self.env['account.journal'].search([('pe_invoice_code', '=', '01')], limit=1)
                journal_id= journal and journal.id or False
            elif invoice_id.state=='draft':
                journal=self.env['account.journal'].search([('pe_invoice_code', '=', '03')], limit=1)
                journal_id= journal and journal.id or False
            if journal_id:
                invoice_id.journal_id = journal_id
            for line in invoice_id.invoice_line_ids:
                line.set_pe_affectation_code()
        return res
    