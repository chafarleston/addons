{
    'name': u'Guias de remisión electrónicas',
    'version': '1.0',
    'author': 'facturaloperú',
    'website': '',
    'category': 'Stock',
    'description': u'''
        Guias de remisión de remitente electrónico
    ''',
    'depends': [
        'stock',
        'delivery'
    ],
    'data': [
        'data/email.xml',
        'data/ir.sequence.csv',
        'report/stock.xml',
        'views/stock.xml',
        'views/stock_picking_serie.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
    'active': False,
}
