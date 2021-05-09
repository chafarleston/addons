# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons.mail.wizard.mail_compose_message import _reopen


class AccountInvoiceSend(models.TransientModel):
    _inherit = 'account.invoice.send'

    @api.onchange('template_id')
    def onchange_template_id(self):
        res = super(AccountInvoiceSend, self).onchange_template_id()
        if self.invoice_ids:
            attachment_ids = self.invoice_ids.mapped(lambda rec: rec.create_attachment())
            self.attachment_ids = self.attachment_ids.ids + attachment_ids[0]
        return res
