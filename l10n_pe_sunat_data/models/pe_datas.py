# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class L10npeDatas(models.Model):
    _name = 'l10n_pe.datas'

    name = fields.Char(string="Name", required=True)
    company_id = fields.Many2one(comodel_name="res.company", string="Company")
    code = fields.Char(string="Code", required=True)
    un_ece_code = fields.Char(string="UN/ECE Code")
    table_code = fields.Char(string="Table Code", required=True)
    active = fields.Boolean(string="Active", default=True)
    percentage = fields.Float(string='Tasa')
    amount_min = fields.Float(string='Monto mínimo')
    description = fields.Text(string="Description")
    
    _sql_constraints = [
        ('table_code_uniq', 'unique(code, table_code)', 'The code of the table must be unique by table code !')
    ]
    
    @api.model
    def get_selection(self, table_code):
        res = list()
        datas = self.search([('table_code', '=', table_code)])
        if datas:
            res = [(data.code, data.name) for data in datas]
        return res
