# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.exceptions import Warning
from odoo.tools import pycompat
import babel
import base64
import copy
import datetime
import dateutil.relativedelta as relativedelta
import logging

class MailTemplate(models.Model):
    _inherit = 'mail.template'

    report_second_name = fields.Char('Second Report Filename', translate=True,
                              help="Name to use for the generated report file (may contain placeholders)\n"
                                   "The extension can be omitted and will then come from the report type.")
    report_second_template = fields.Many2one('ir.actions.report', 'Optional report to print and attach')
