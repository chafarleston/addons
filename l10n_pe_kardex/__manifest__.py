# -*- coding: utf-8 -*-
{
    'name': 'Reporte Kardex',
    'version': '1.0.1',
    'category': 'Stock',
    'sequence': 22,
    'summary': 'Reporte Kardex',
    'author': u"FacturaloPerú S.A.C",
    'description': """
          Reporte Kardex
    """,
    'depends': [
        'stock',
        'report_xlsx',
        'product_expiry'
    ],
    'data': [
        'views/kardex_view.xml',
        'views/assets.xml',
        'security/ir.model.access.csv'
    ],
    'qweb': [
        'static/src/xml/kardex.xml'
    ],
    'installable': True,
    'application': True,
    'website': 'https://www.odoo.com/page/stock',
}
