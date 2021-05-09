# -*- encoding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    l10n_pe_document_type = fields.Selection(selection='_l10n_pe_get_sunat_code', string='Tipo de documento')
    l10n_pe_document_number = fields.Char(string='Número de documento')
    l10n_pe_tradename = fields.Char(string='Nombre comercial')
    l10n_pe_legal_name = fields.Char(string='Nombre legal')
    l10n_pe_sunat_type = fields.Char(string='Tipo de contribuyente', default='-')
    l10n_pe_sunat_state = fields.Char(string='Estado de contribuyente', default='-')
    l10n_pe_sunat_date_inscription = fields.Date(string='Fecha de inscripción', default=fields.Date().today())
    l10n_pe_sunat_date_start = fields.Date(string='Fecha de inicio de activades', default=fields.Date().today())

    @api.multi
    def name_get(self):
        res = super(ResPartner, self).name_get()
        if self.filtered(lambda w: w.l10n_pe_document_number or w.l10n_pe_document_type):
            return self.mapped(lambda w: (w.id, u'{}'.format(w.name)))
        return res

    @api.model
    def default_get(self, fields_list):
        res = super(ResPartner, self).default_get(fields_list)
        country = self.env['res.country'].search([('code', '=', 'PE')], limit=1)
        res.update({'country_id': country and country.id  or False})
        return res

    @api.model
    def create(self, vals):
        l10n_pe_document_number = vals.get('l10n_pe_document_number', '')
        l10n_pe_document_type = vals.get('l10n_pe_document_type', '')
        if len(l10n_pe_document_number) == 11 and l10n_pe_document_type == '6':
            vals.update({
                'company_type': 'company',
                'image': self._get_default_image('company', 1, False)
            })
        return super(ResPartner, self).create(vals)

    @api.model
    def _l10n_pe_get_sunat_code(self):
        return self.env['l10n_pe.datas'].get_selection("PE.CPE.CATALOG6")

    @api.multi
    def l10n_pe_is_company_partner(self):
        return self == self.env.user.company_id.partner_id

    @api.constrains('l10n_pe_document_type', 'l10n_pe_document_number')
    def _check_l10n_pe_document(self):
        for record in self:
            if record.l10n_pe_document_type in ['6'] and len(record.l10n_pe_document_number) == 11:
                factor = '5432765432'
                sum = 0
                for f in range(0, 10):
                    sum += int(factor[f]) * int(record.l10n_pe_document_number[f])

                subtraction = 11 - (sum % 11)
                if subtraction == 10:
                    dig_check = 0
                elif subtraction == 11:
                    dig_check = 1
                else:
                    dig_check = subtraction
                if int(record.l10n_pe_document_number[10]) != dig_check:
                    raise ValidationError('El RUC ingresado es incorrecto')
            elif record.l10n_pe_document_type in ['6'] and len(record.l10n_pe_document_number) != 11:
                    raise ValidationError('El RUC ingresado es incorrecto')
            elif record.l10n_pe_document_type in ['1'] and len(record.l10n_pe_document_number) != 8:
                raise ValidationError('El DNI ingresado es incorrecto')

    @api.onchange('l10n_pe_document_type', 'l10n_pe_document_number')
    def _onchange_l10n_pe_document(self):
        if self.l10n_pe_document_type and self.l10n_pe_document_number:
            res = self.l10n_pe_get_data(self.l10n_pe_document_type, self.l10n_pe_document_number)
            self.update(res)

    @api.model
    def l10n_pe_get_data(self, document_type, document_number):
        return {}


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_pe_document_type = fields.Selection(related='partner_id.l10n_pe_document_type', string='Tipo de documento')
    l10n_pe_document_number = fields.Char(related='partner_id.l10n_pe_document_number', string='Número de documento')

