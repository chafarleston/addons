from odoo import fields, models

ONE = '1'
EIGTH = '8'
NINE = '9'
STATE_SUNAT_SELECTION = [
    (ONE, '1'),
    (EIGTH, '8'),
    (NINE, '9')
]

TYPE_A = 'A'
TYPE_M = 'M'
TYPE_C = 'C'
TYPE_SUNAT_SELECTION =[
    (TYPE_A, 'Apertura del ejercicio'),
    (TYPE_M, 'Movimiento del mes'),
    (TYPE_C, 'Cierre del ejercicio')
]

BALANCE = 'balance'
LOSS_GAIN = 'loss_gain'

TYPE_PLAN_SELECTION = [
    (BALANCE, 'Cuentas del balance general'),
    (LOSS_GAIN, 'Cuentas de ganancia y pérdidas')
]
CASH = 'cash'
CURRENT_ACCOUNT = 'current_account'
TYPE_BOX = [
    (CASH, 'Efectivo'),
    (CURRENT_ACCOUNT, 'Cuenta corriente')
]


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_pe_operation_state_sunat = fields.Selection(selection=STATE_SUNAT_SELECTION,
                                                     string='Estado de la operacion sunat', default='1')
    l10n_pe_operation_type_sunat = fields.Selection(selection=TYPE_SUNAT_SELECTION, string='Tipo de operación sunat',
                                                    default=TYPE_M)


class AccountAccountType(models.Model):
    _inherit = 'account.account.type'

    l10n_pe_type_plan = fields.Selection(selection=TYPE_PLAN_SELECTION, string='Tipo segun plan contable',
                                         default=BALANCE)
    l10n_pe_type_box = fields.Selection(selection=TYPE_BOX, string='Tipo de caja', default=CASH)
