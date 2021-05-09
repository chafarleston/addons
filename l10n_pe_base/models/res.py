# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from . import amount_to_text_es

import re
import requests

SUNAT = 'sunat'
PURCHASE = 'purchase'
SALE = 'sale'

L10N_SOURCE_RATE = [
    (SUNAT, 'Sunat')
]

L10N_PE_TYPES = [
    (PURCHASE, 'Compra'),
    (SALE, 'Venta')
]


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    l10n_pe_rate = fields.Float(string='Tasa', digits=(10, 3), compute='_compute_l10n_pe_rate')
    l10n_pe_plural_name = fields.Char(string="Plural de divisa")
    l10n_pe_type = fields.Selection(L10N_PE_TYPES, string='Tipo', default='sale')
    l10n_pe_source_rate = fields.Selection(selection=L10N_SOURCE_RATE, string='Origen del TC')

    _sql_constraints = [
        ('unique_name', 'unique (name, l10n_pe_type)', 'La moneda y el tipo de ser unico!'),
    ]

    @api.multi
    def name_get(self):
        return self.mapped(lambda record: (record.id, u'{} {}'.format(record.name, dict(L10N_PE_TYPES).get(record.l10n_pe_type, ''))))

    @api.multi
    def l10n_pe_is_company_currency(self):
        return self == self.env.user.company_id.currency_id

    @api.model
    def l10n_pe_get_currency(self):
        currencies = self.search([('l10n_pe_source_rate', '!=', False)])
        currencies.mapped(lambda w: w._l10n_pe_from_sunat() if w.l10n_pe_source_rate == SUNAT else None)

    @api.multi
    def _l10n_pe_from_sunat(self):
        param = self.env['ir.config_parameter'].sudo().get_param
        url = param('host_currency_sunat_url', False)
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'lxml')
        index = -1 if self.l10n_pe_type == SALE else -2
        res = soup.find_all('td', {'align': 'center', 'class': 'tne10'})[index]
        value = re.sub('[\r\n\t]', '', res.text)
        if self and value and value.strip() and self.name in ['USD']:
            obj_currency_rate = self.rate_ids.filtered(
                lambda x: fields.Datetime.from_string(x.name).strftime('%Y-%m-%d') == fields.Date().today()
            )
            if not obj_currency_rate:
                self.env['res.currency.rate'].create({
                    'name': fields.Datetime().now(),
                    'l10n_pe_rate': float(value.strip()),
                    'currency_id': self.id,
                    'rate': 1 / float(value.strip())
                })

    @api.depends('rate')
    def _compute_l10n_pe_rate(self):
        self.mapped(lambda w: w.update({'l10n_pe_rate': 1.0 / w.rate}))

    @api.multi
    def l10n_pe_get_rate_by_date(self, date):
        if self != self.env.user.company_id.currency_id and date:
            rate_obj = self.env['res.currency.rate'].search([('currency_id', '=', self.id), ('name', '<=', date)], order='name DESC', limit=1)
            if rate_obj:
                return rate_obj.l10n_pe_rate
            elif self:
                raise ValidationError('Configure un tipo de cambio para moneda {} con fecha {}'.format(self.name, date))
        else:
            return 1

    @api.multi
    def l10n_pe_compute_by_date(self, to_currency, date):
        current_currency_rate = self.l10n_pe_get_rate_by_date(date)
        to_currency_rate = to_currency.l10n_pe_get_rate_by_date(date)
        return to_currency_rate / current_currency_rate

    @api.multi
    def amount_to_text(self, amount):
        self.ensure_one()
        if 1 <= amount < 2:
            currency = self.currency_unit_label or self.l10n_pe_plural_name or self.name or ""
        else:
            currency = self.l10n_pe_plural_name or self.name or ""
        sufix = self.currency_subunit_label or ""
        amount_text = amount_to_text_es.amount_to_text(amount, currency, sufix, True)
        return amount_text


class ResCurrencyRate(models.Model):
    _inherit = 'res.currency.rate'

    l10n_pe_rate = fields.Float(string='Tasa', digits=(10, 3), default=1)

    @api.model
    def default_get(self, fields_list):
        res = super(ResCurrencyRate, self).default_get(fields_list)
        res.update({
            'name': fields.Date().context_today(self)
        })
        return res

    @api.model
    def create(self, vals):
        res = super(ResCurrencyRate, self.with_context(l10n_pe_no_write=True)).create(vals)
        res.update({'rate': 1.0 / (res.l10n_pe_rate or 1)})
        return res

    @api.multi
    def write(self, vals):
        res = super(ResCurrencyRate, self).write(vals)
        if not self.env.context.get('l10n_pe_no_write', False):
            self.with_context(l10n_pe_no_write=True).mapped(lambda x: x.update({'rate': 1.0 / (x.l10n_pe_rate or 1)}))
        return res
