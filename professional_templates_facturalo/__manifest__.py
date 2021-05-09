# -*- coding: utf-8 -*-
{
    'name': "Professional Report Templates",
    'license': 'OPL-1',
    'support': 'support@optima.co.ke',
    'summary': """
        Professional Report Templates: Purchase Order, RFQ, Sales Order, Quotation, Invoice, Delivery Note and Picking List
        """,
    'description': """ """,
    'author': "Facturalo",
    'website': "",
    'category': 'Accounting & Finance',
    'images': ['static/description/main.png'],
    'version': '12.0.1.5',
    'price': 149,
    'currency': 'EUR',
    # any module necessary for this one to work correctly
    'depends': ['professional_templates', 'l10n_pe_facturalo'],
    # always loaded
    'data': [
        'invoice/cubic_template.xml',
        'invoice/dl_envelope.xml',
        'invoice/invoice_lines.xml',
        'invoice/military_template.xml',
        'invoice/retro_template.xml',
        'picking/cubic_template.xml',
        'picking/military_template.xml',
        'picking/retro_template.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo.xml',
    ],
    'installable':
    True,
    'auto_install':
    False,
    'application':
    True,
}
