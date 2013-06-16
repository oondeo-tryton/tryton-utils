#!/usr/bin/python

import sys
import os
import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal

directory = os.path.abspath(os.path.normpath(os.path.join(os.getcwd(),
                    'trytond')))

if os.path.isdir(directory):
    sys.path.insert(0, directory)

from proteus import config, Model, Wizard

today = datetime.date.today()
now = datetime.datetime.now()


module = sys.argv[1]
database=None
if len(sys.argv) > 2:
    database = sys.argv[2]

config = config.set_trytond(database, database_type='postgresql',
    password='admin')


def install_module(module):
    '''Install client module with dependencies.'''
    Module = Model.get('ir.module.module')
    (module,) = Module.find([('name', '=', module)])
    Module.install([module.id], config.context)
    Wizard('ir.module.module.install_upgrade').execute('upgrade')


def create_company():
    Currency = Model.get('currency.currency')
    CurrencyRate = Model.get('currency.currency.rate')
    Company = Model.get('company.company')
    Party = Model.get('party.party')

    company_config = Wizard('company.company.config')
    company_config.execute('company')
    company = company_config.form
    party = Party(name='<your company>')
    party.save()
    company.party = party

    currencies = Currency.find([('code', '=', 'EUR')])
    if not currencies:
        currency = Currency(name='EUR0', symbol=u'$', code='EUR',
            rounding=Decimal('0.01'), mon_grouping='[3,3,0]',
            mon_decimal_point='.')
        currency.save()
        CurrencyRate(date=today + relativedelta(month=1, day=1),
            rate=Decimal('1.0'), currency=currency).save()
    else:
        currency, = currencies

    company.currency = currency
    company_config.execute('add')
    company, = Company.find([])

    User = Model.get('res.user')
    config._context = User.get_preferences(True, config.context)


def create_fiscal_year():
    FiscalYear = Model.get('account.fiscalyear')
    Sequence = Model.get('ir.sequence')
    Company = Model.get('company.company')
    company, = Company.find([])
    fiscalyear = FiscalYear(name='%s' % today.year)
    fiscalyear.start_date = today + relativedelta(month=1, day=1)
    fiscalyear.end_date = today + relativedelta(month=12, day=31)
    fiscalyear.company = company
    post_move_sequence = Sequence(name='%s' % today.year,
         code='account.move', company=company)
    post_move_sequence.save()
    fiscalyear.post_move_sequence = post_move_sequence
    fiscalyear.save()
    FiscalYear.create_period([fiscalyear.id], config.context)


def create_chart_of_accounts():
    AccountTemplate = Model.get('account.account.template')
    Account = Model.get('account.account')
    Company = Model.get('company.company')
    company, = Company.find([])
    account_template, = AccountTemplate.find([('parent', '=', False)])
    create_chart = Wizard('account.create_chart')
    create_chart.execute('account')
    create_chart.form.account_template = account_template
    create_chart.form.company = company
    create_chart.execute('create_account')
    receivable, = Account.find([
             ('kind', '=', 'receivable'),
             ('company', '=', company.id),
             ])
    payable, = Account.find([
             ('kind', '=', 'payable'),
             ('company', '=', company.id),
             ])
    revenue, = Account.find([
             ('kind', '=', 'revenue'),
             ('company', '=', company.id),
             ])
    expense, = Account.find([
             ('kind', '=', 'expense'),
             ('company', '=', company.id),
             ])
    cash, = Account.find([
             ('kind', '=', 'other'),
             ('company', '=', company.id),
             ('name', '=', 'Main Cash'),
             ])
    create_chart.form.account_receivable = receivable
    create_chart.form.account_payable = payable
    create_chart.execute('create_properties')

if __name__ == "__main__":

    install_module(module)
    create_company()
    create_fiscal_year()
    create_chart_of_accounts()



