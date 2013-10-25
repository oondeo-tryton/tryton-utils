#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import argparse
import datetime
import logging
import os
import sys
from dateutil.relativedelta import relativedelta

directory = os.path.abspath(os.path.normpath(os.path.join(os.getcwd(),
                    'trytond')))
proteus_directory = os.path.abspath(os.path.normpath(os.path.join(os.getcwd(),
                    'proteus')))

if os.path.isdir(directory):
    sys.path.insert(0, directory)
if os.path.isdir(proteus_directory):
    sys.path.insert(0, proteus_directory)

from proteus import (
    config as pconfig,
    Model,
    Wizard)

TODAY = datetime.date.today()
NOW = datetime.datetime.now()

logger = logging.getLogger('Startup')


def parse_arguments():
    #usage = 'usage: %prog [options] <database>'
    #parser = argparse.ArgumentParser(usage=usage)
    parser = argparse.ArgumentParser()
    parser.add_argument('database')
    parser.add_argument('--module', '-m', metavar='MODULE_NAME',
        dest='modules', action='append',
        help='module that will be installed/upgraded.')
    parser.add_argument('--demo', action='store_true',
        help='create demo data after create real data')
    parser.add_argument('--only-demo', action='store_true',
        help='only create demo date. Database must exists with real data '
        'created')
    parser.add_argument('--verbose', '-v', action='store_true',
        help='Print more verbose log messages', default=False)

    settings = parser.parse_args()

    if settings.verbose:
        logger.setLevel(logging.DEBUG)
        logging.basicConfig(stream=sys.stderr, level=logging.ERROR)
    else:
        logger.setLevel(logging.INFO)
        logging.basicConfig(stream=sys.stderr, level=logging.ERROR)

    return settings


def connect_database(database, password='admin', database_type='postgresql'):
    return pconfig.set_trytond(database, database_type=database_type,
        password=password, config_file='trytond/etc/trytond.conf')


def install_modules(config, modules):
    '''
    Function get from tryton_demo.py in tryton-tools repo:
    http://hg.tryton.org/tryton-tools
    '''
    Module = Model.get('ir.module.module')
    modules = Module.find([
        ('name', 'in', modules),
        #('state', '!=', 'installed'),
    ])
    Module.install([x.id for x in modules], config.context)
    modules = [x.name for x in Module.find([
                ('state', 'in', ('to install', 'to_upgrade')),
                ])]
    Wizard('ir.module.module.install_upgrade').execute('upgrade')

    ConfigWizardItem = Model.get('ir.module.module.config_wizard.item')
    for item in ConfigWizardItem.find([('state', '!=', 'done')]):
        item.state = 'done'
        item.save()

    installed_modules = [m.name
        for m in Module.find([('state', '=', 'installed')])]
    return modules, installed_modules


def create_party(config, name, street=None, zip=None, city=None,
        subdivision_code=None, country_code='ES', phone=None, website=None):
    Address = Model.get('party.address')
    ContactMechanism = Model.get('party.contact_mechanism')
    Country = Model.get('country.country')
    Party = Model.get('party.party')
    Subdivision = Model.get('country.subdivision')

    parties = Party.find([('name', '=', name)])
    if parties:
        return parties[0]

    country, = Country.find([('code', '=', country_code)])
    if subdivision_code:
        subdivision, = Subdivision.find([('code', '=', subdivision_code)])
    else:
        subdivision = None

    party = Party(name=name)
    party.addresses.pop()
    party.addresses.append(
        Address(street=street,
            zip=zip,
            city=city,
            country=country,
            subdivision=subdivision))
    if phone:
        party.contact_mechanisms.append(
            ContactMechanism(type='phone',
                value=phone))
    if website:
        party.contact_mechanisms.append(
            ContactMechanism(type='website',
                value=website))

    party.save()
    return party


def create_company(config, name, street=None, zip=None, city=None,
        subdivision_code=None, country_code='ES', currency_code='EUR',
        phone=None, website=None):
    '''
    Based on tryton_demo.py in tryton-tools repo:
    http://hg.tryton.org/tryton-tools
    '''
    Company = Model.get('company.company')
    Currency = Model.get('currency.currency')

    party = create_party(config, name, street=street, zip=zip, city=city,
        subdivision_code=subdivision_code, country_code=country_code,
        phone=phone, website=website)

    companies = Company.find([('party', '=', party.id)])
    if companies:
        return companies[0]

    currency, = Currency.find([('code', '=', currency_code)])

    company_config = Wizard('company.company.config')
    company_config.execute('company')
    company = company_config.form
    company.party = party
    company.currency = currency
    company_config.execute('add')

    # Reload context
    User = Model.get('res.user')
    config._context = User.get_preferences(True, config.context)

    company, = Company.find([('party', '=', party.id)])
    return company


def create_chart_of_accounts(config, template_name, company):
    AccountTemplate = Model.get('account.account.template')
    Account = Model.get('account.account')

    root_accounts = Account.find([('parent', '=', None)])
    if root_accounts:
        return

    account_templates = AccountTemplate.find([
            ('name', '=', template_name),
            ('parent', '=', None),
            ])
    assert len(account_templates) == 1, ('Unexpected num of root templates '
        'with name "%s": %s' % (template_name, account_templates))

    create_chart = Wizard('account.create_chart')
    create_chart.execute('account')
    create_chart.form.account_template = account_templates[0]
    create_chart.form.company = company
    create_chart.execute('create_account')

    receivable = Account.find([
            ('kind', '=', 'receivable'),
            ('company', '=', company.id),
            ])
    receivable = receivable[0]
    payable = Account.find([
            ('kind', '=', 'payable'),
            ('company', '=', company.id),
            ])[0]
    #revenue, = Account.find([
    #        ('kind', '=', 'revenue'),
    #        ('company', '=', company.id),
    #        ])
    #expense, = Account.find([
    #        ('kind', '=', 'expense'),
    #        ('company', '=', company.id),
    #        ])
    #cash, = Account.find([
    #        ('kind', '=', 'other'),
    #        ('company', '=', company.id),
    #        ('name', '=', 'Main Cash'),
    #        ])
    create_chart.form.account_receivable = receivable
    create_chart.form.account_payable = payable
    create_chart.execute('create_properties')
    # TODO: return create_chart


def create_fiscal_year(config, company, year=None):
    FiscalYear = Model.get('account.fiscalyear')
    Module = Model.get('ir.module.module')
    Sequence = Model.get('ir.sequence')
    SequenceStrict = Model.get('ir.sequence.strict')

    if year is None:
        year = TODAY.year

    installed_modules = [m.name
        for m in Module.find([('state', '=', 'installed')])]

    post_move_sequence = Sequence.find([
            ('name', '=', '%s' % year),
            ('code', '=', 'account_move'),
            ('company', '=', company.id),
            ])
    if post_move_sequence:
        post_move_sequence = post_move_sequence[0]
    else:
        post_move_sequence = Sequence(name='%s' % year,
            code='account.move', company=company)
        post_move_sequence.save()

    fiscalyear = FiscalYear.find([
            ('name', '=', '%s' % year),
            ('company', '=', company.id),
            ])
    if fiscalyear:
        fiscalyear = fiscalyear[0]
    else:
        fiscalyear = FiscalYear(name='%s' % year)
        fiscalyear.start_date = TODAY + relativedelta(month=1, day=1)
        fiscalyear.end_date = TODAY + relativedelta(month=12, day=31)
        fiscalyear.company = company
        fiscalyear.post_move_sequence = post_move_sequence
        if 'account_invoice' in installed_modules:
            for attr, name in (('out_invoice_sequence', 'Invoice'),
                    ('in_invoice_sequence', 'Supplier Invoice'),
                    ('out_credit_note_sequence', 'Credit Note'),
                    ('in_credit_note_sequence', 'Supplier Credit Note')):
                sequence = SequenceStrict.find([
                        ('name', '=', '%s %s' % (name, year)),
                        ('code', '=', 'account.invoice'),
                        ('company', '=', company.id),
                        ])
                if sequence:
                    sequence = sequence[0]
                else:
                    sequence = SequenceStrict(
                        name='%s %s' % (name, year),
                        code='account.invoice',
                        company=company)
                    sequence.save()
                setattr(fiscalyear, attr, sequence)
        fiscalyear.save()

    if not fiscalyear.periods:
        FiscalYear.create_period([fiscalyear.id], config.context)

    return fiscalyear


def create_analytic_account(name, type, parent):
    Account = Model.get('analytic_account.account')
    account = Account(name=name,
        type=type,
        state='opened',
        root=parent and parent.root or parent,
        parent=parent,
        display_balance='credit-debit')
    return account


def create_location(name, type, parent=None, code=None, address=None):
    Location = Model.get('stock.location')

    location = Location.find([
            ('name', '=', name),
            ('parent', '=', parent and parent.id or None),
            ])
    if location:
        return location[0]
    else:
        return Location(type=type,
            name=name,
            code=code,
            parent=parent,
            address=address)


def create_warehouse(name, code=None, address=None,
        separate_input=False, separate_output=False):
    warehouse = create_location(name, 'warehouse', code=code, address=address)

    storage_location = create_location('%s Storage' % name, 'storage')
    storage_location.save()
    warehouse.storage_location = storage_location

    production_location = create_location('%s Production' % name, 'production')
    production_location.save()
    warehouse.production_location = production_location

    if separate_input:
        input_location = create_location('%s Input' % name, 'storage')
        input_location.save()
        warehouse.input_location = input_location
    else:
        warehouse.input_location = storage_location

    if separate_output:
        output_location = create_location('%s Output' % name, 'storage')
        output_location.save()
        warehouse.output_location = output_location
    else:
        warehouse.output_location = storage_location

    return warehouse


def remove_warehouse_and_locations(warehouse):
    Location = Model.get('stock.location')

    warehouse.type = 'storage'
    warehouse.save()

    for warehouse_loc in Location.find([('parent', 'child_of', warehouse.id)]):
        Location.delete(warehouse_loc)


if __name__ == "__main__":
    settings = parse_arguments()

    config = connect_database(settings.database)
    if not settings.modules:
        sys.exit()

    inst_upg_modules, installed_modules = install_modules(config,
        settings.modules)
    logger.info('Modules installed or upgraded: %s' % inst_upg_modules)
    logger.debug('All installed modules: %s' % installed_modules)

    if not settings.only_demo:
        logger.info('Load start data in %s' % settings.database)

        if 'company' in installed_modules:
            company = create_company(config, u'NaN·tic')
        logger.info('Company created: %s' % company)

        # TODO: create_nantic_user(config)

        if 'account_es_pyme' in installed_modules:
            create_chart_of_accounts(config,
                'Plan General Contable PYMES 2008', company)
            logger.info('Chart of accounts created')
        elif 'account' in installed_modules:
            create_chart_of_accounts(config, 'Minimal Account Chart', company)
            logging.getLogger('Xarxafarma').info('Chart of accounts created')

        if 'account' in installed_modules:
            fiscalyear = create_fiscal_year(config, company)
            logging.getLogger('Xarxafarma').info('Fiscal year created: %s'
                % fiscalyear)
