# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning
import base64

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    @api.onchange('invoice_line_ids','invoice_line_ids.invoice_line_tax_ids')
    def tax_free(self):
        valor=False
        for line in self.invoice_line_ids:
          price_total= line.price_total
          price_subtotal= line.price_subtotal

          for l in line.invoice_line_tax_ids:
            if l.name =='Gratuito':
              valor = True
            else:
              valor= False
          if valor == True:
            line.price_total=0
            line.price_subtotal=0
          else:
            line.price_total= price_total
            line.price_subtotal= price_subtotal


    @api.multi
    def write(self, vals):
        res = super(AccountInvoice, self).write(vals)
        self.tax_free()
        return res

    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self,vals):
        res = super(AccountInvoice, self).create(vals)
        res.tax_free()
        return res
