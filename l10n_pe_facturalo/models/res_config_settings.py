# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields,  models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_uom = fields.Boolean("Units of Measure", implied_group='uom.group_uom', default=True)
