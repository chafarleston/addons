# -*- coding: utf-8 -*-
from odoo import fields, models


class PosConfigNetworkPrinter(models.Model):
    _inherit = 'pos.config'

    iface_enable_network_printing = fields.Boolean(
        "Enable IP Network Printing",
        default=True,
        help="If you enable network printing,\
            Printing via IoT Box will be given second priority")
    iface_network_printer_ip_address = fields.Char('IP Address', size=45)
    iface_network_printer_port = fields.Integer('Port', default='9100')
