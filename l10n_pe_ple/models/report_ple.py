from odoo import api, fields, models
from odoo.exceptions import UserError

_STATES_READONLY = {
        'validated': [('readonly', True)],
        'declared': [('readonly', True)]
}

DRAFT = 'draft'
VALIDATED = 'validated'
DECLARED = 'declared'

STATE_SELECTION = [
    (DRAFT, 'Borrador'),
    (VALIDATED, 'Validado'),
    (DECLARED, 'Declarado')
]


CLOSE_OPERATION = '0'
FACTORY = '1'
CLOSED = '2'

OPERATION_INDICATOR_SELECTION = [
    (CLOSE_OPERATION, 'Cierre de operaciones - baja de inscripción en el RUC'),
    (FACTORY, 'Empresa o entidad operativa'),
    (CLOSED, 'Cierre del libro ')
]

WITH_INFO = '1'
WITHOUT_INFO = '0'
INDICATOR_CONTENT_SELECTION = [
    (WITH_INFO, 'Con información'),
    (WITHOUT_INFO, 'Sin información')
]

NORMAL = 'normal'
SIMPLIFIED = 'simplified'

TYPE_REPORT_SELECTION = [
    (NORMAL, 'Normal'),
    (SIMPLIFIED, 'Simplificado')
]


class ReportPle(models.Model):
    _name = 'report.ple'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'report.report_xlsx.abstract']
    _description = 'Reporte ple'

    name = fields.Char(string='Nombre', states=_STATES_READONLY)
    file_txt = fields.Binary(string='Archivo TXT', readonly=True)
    filename_txt = fields.Char(string='Nombre del archivo TXT')
    code = fields.Char(string='Código', readonly=True, track_visibility='onchange', states=_STATES_READONLY)
    state = fields.Selection(selection=STATE_SELECTION, string='Estado', default=DRAFT, track_visibility='onchange')
    range_id = fields.Many2one(comodel_name='date.range', string='Periodo', required=True, states=_STATES_READONLY)
    period_special = fields.Boolean(string='Apertura/Cierre', states=_STATES_READONLY)
    file_simplified = fields.Binary(string='Archivo TXT simplificado', readonly=True)
    indicator_operation = fields.Selection(selection=OPERATION_INDICATOR_SELECTION, string='Indicador de operaciones',
                                           default=CLOSE_OPERATION, required=True, track_visibility='onchange',
                                           states=_STATES_READONLY)
    indicator_content = fields.Selection(selection=INDICATOR_CONTENT_SELECTION, string='Indicador del contenido',
                                         default=WITH_INFO, required=True, track_visibility='onchange',
                                         states=_STATES_READONLY)
    currency_id = fields.Many2one(comodel_name='res.currency', string='Moneda', domain=[('name', 'in', ['PEN', 'USD'])],
                                  default=lambda self: self.env.user.company_id.currency_id, required=True,
                                  track_visibility='onchange', states=_STATES_READONLY)
    company_id = fields.Many2one(comodel_name='res.company', string='Compañía',
                                 default=lambda self: self.env.user.company_id, required=True, states=_STATES_READONLY)
    type_report = fields.Selection(selection=TYPE_REPORT_SELECTION, string='Tipo de reporte', default=NORMAL,
                                   states=_STATES_READONLY)

    @api.model
    def default_get(self, fields_list):
        if not self.env.user.company_id.partner_id.vat:
            raise UserError(u'Configure número de documento de la compañía')
        res = super(ReportPle, self).default_get(fields_list)
        today = fields.Date().context_today(self)
        range_obj = self.env['date.range'].search([('date_start', '<=', today), ('date_end', '>=', today)], limit=1)
        if not range_obj:
            raise UserError('No existe periodo para esta fecha, configure en rango de fechas')
        res.update({'range_id': range_obj and range_obj.id or False})
        return res

    @api.multi
    def action_generate_ple(self, value):
        value.update({'state': 'validated'})
        self.write(value)

    @api.multi
    def action_declare(self):
        self.write({'state': 'declared'})

    @api.model
    def get_year_month(self, date):
        from_date = fields.Date().from_string(date)
        return '{}{}'.format(from_date.year, from_date.month) if date else ''
