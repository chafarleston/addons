from base64 import encodestring
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    l10n_pe_number = fields.Char(string='Serie', readonly=True, copy=False)
    l10n_pe_date_emission = fields.Datetime(string='Fecha de emision',
                                            default=fields.Datetime().to_string(fields.Datetime.now()))
    l10n_pe_date_start = fields.Date(string=u'Fecha de inicio',
                                     default=fields.Datetime().to_string(fields.Datetime.now()))
    l10n_pe_observation = fields.Text(string='Observaciones')
    l10n_pe_addressee_id = fields.Many2one(comodel_name='res.partner', string='Destinatario')
    l10n_pe_third_partner_id = fields.Many2one(comodel_name='res.partner', string='Tercero')
    l10n_pe_carrier_id = fields.Many2one(comodel_name='res.partner', string='Transportista')
    l10n_pe_driver_id = fields.Many2one(comodel_name='res.partner', string='Conductor')
    l10n_pe_car_detail_ids = fields.One2many(comodel_name='l10n_pe.car.detail', inverse_name='picking_id',
                                             string=u'Vehículo')
    l10n_pe_container = fields.Char(string='Contenedor')
    l10n_pe_shipment = fields.Char(string=u'Puerto o aeropuerto de embarque')
    l10n_pe_disembarkation = fields.Char(string=u'Puerto o aeropuerto de desembarque')
    l10n_pe_send_sunat = fields.Boolean(compute='_compute_send_sunat')
    l10n_pe_indicator = fields.Boolean(string='Indicador del transbordo programado')
    l10n_pe_gross_weight = fields.Float(string='Peso bruto')
    l10n_pe_related_document = fields.Selection(selection='_get_l10_pe_related_document', string='Document relacionado',
                                                default='06')
    l10n_pe_related_document_number = fields.Char(string=u'Número de documento relacionado', default='-')
    l10n_pe_operation_type = fields.Selection(selection='_get_l10n_pe_operation_type', string='Motivo de traslado',
                                              default='01')
    l10n_pe_model_move = fields.Selection(selection='_get_l10n_pe_model_move', string='Modalidad de traslado',
                                          default='01')
    l10n_pe_number_of_packages = fields.Float(string='Número de paquetes')

    documentointerno  = fields.Boolean(string='Documento Interno')
    l10n_pe_is_internal_document  = fields.Boolean(string='Documento Interno')

    l10n_pe_internal_serie_id = fields.Many2one(comodel_name='stock.picking.serie', string='Serie')

    l10n_pe_internal_number = fields.Char(string='Correlativo')

    @api.depends('picking_type_id.warehouse_id.l10n_pe_send_sunat', 'picking_type_id', 'state')
    def _compute_send_sunat(self):
        self.mapped(lambda w: w.update({
            'l10n_pe_send_sunat': (w.picking_type_id.warehouse_id.l10n_pe_send_sunat and
                                   w.picking_type_id.code in ['outgoing'] and w.state in ['done'])
        }))

    @api.model
    def _get_l10_pe_related_document(self):
        return self.env['l10n_pe.datas'].get_selection('PE.CPE.CATALOG21')

    @api.model
    def _get_l10n_pe_operation_type(self):
        return self.env['l10n_pe.datas'].get_selection('PE.CPE.CATALOG20')

    @api.model
    def _get_l10n_pe_model_move(self):
        return self.env['l10n_pe.datas'].get_selection('PE.CPE.CATALOG18')

    @api.multi
    def _get_document_name(self):
        return '{}-{}-{}'.format(
            self.env.user.company_id.partner_id.l10n_pe_document_number,
            '09',
            self.l10n_pe_number
        )

    @api.multi
    def action_stock_cpe_send(self):
        template = self.env.ref('l10n_cpe_stock.email_template_stock_cpe', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        attach = dict()
        result_pdf, type = self.env['ir.actions.report']._get_report_from_name(
            'l10n_cpe_stock.report_stock_picking_cpe').render_qweb_pdf(self.ids)
        attach['name'] = '%s.pdf' % self._get_document_name()
        attach['type'] = 'binary'
        attach['datas'] = encodestring(result_pdf)
        attach['datas_fname'] = '%s.pdf' % self._get_l10n_pe_document_name()
        attach['res_model'] = 'mail.compose.message'
        attachment_id = self.env['ir.attachment'].create(attach)
        attachment_ids = list()
        attachment_ids.append(attachment_id.id)
        file_binary_utf8 = self.sunat_ids.filtered(lambda w: w.code_sunat == '0' and w.cdr_sunat)[0].file_binary_utf8
        attach = dict()
        attach['name'] = '%s.xml' % self._get_l10n_pe_document_name()
        attach['type'] = 'binary'
        attach['datas'] = file_binary_utf8
        attach['datas_fname'] = '%s.xml' % self._get_document_name()
        attach['res_model'] = 'mail.compose.message'
        attachment_id = self.env['ir.attachment'].create(attach)
        attachment_ids.append(attachment_id.id)
        ctx = dict(
            default_model=self._name,
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            force_email=True,
            default_attachment_ids=[(6, 0, attachment_ids)]
        )
        return {
            'name': 'Componer correo electrónico',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }


class CarDetail(models.Model):
    _name = 'l10n_pe.car.detail'

    code = fields.Char(string='Placa', required=True)
    name = fields.Char(string='Nombre')
    picking_id = fields.Many2one(comodel_name='stock.picking', string='Stock', required=True)


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def build_l10n_pe_data_line_guide(self):
        list_line = list()
        for record in self:
            if not record.product_id.default_code:
                raise ValidationError('Incorrecto, referencia interna de producto')
            if not record.product_uom.sunat_code_id:
                raise ValidationError('Incorrecto, unidad de medida Sunat')

            list_line.append({
                'unit_code': record.product_uom.l10n_pe_sunat_code_id.name,
                'quantity': record.product_uom_qty,
                'description': record.name,
                'item_cod': record.product_id.default_code
            })
        return list_line


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    l10n_pe_send_sunat = fields.Boolean(string='Enviar a sunat')
    l10n_pe_sequence_id = fields.Many2one(comodel_name='ir.sequence', string='Secuencia')
    l10n_pe_code = fields.Char(string='Código de domicilio fiscal')
    picking_id = fields.Many2one(comodel_name='stock.picking', string='Stock', required=True)
    documentointerno = fields.Boolean(string='Documento Interno', related="picking_id.documentointerno")


class StockPickingSerie(models.Model):
    _name = 'stock.picking.serie'
    _rec_name = 'display_name'

    name = fields.Char('Serie', size=4, required=True)
    description = fields.Char('Descripción', required=True)
    establishment_id = fields.Many2one(
        'stock.warehouse', 'Almacen',
        required=True
    )

    display_name = fields.Char(
        string='display name',
        compute='_compute_display_name'
    )

    @api.one
    @api.depends('name', 'establishment_id',)
    def _compute_display_name(self):
        if self.name and self.establishment_id:
            establishment_id = self.establishment_id
            name = self.name
            self.display_name = establishment_id.name+' - '+name
