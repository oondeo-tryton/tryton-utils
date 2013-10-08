#!/usr/bin/env python
# -*- coding: utf-8 -*-

##############################################################################
# Copyright (C) 2013 NaN·tic
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################

import warnings
import sys
import os
import optparse
import logging


def parse_arguments(arguments):
    parser = optparse.OptionParser(usage='xmls-create.py [options] module')
    parser.add_option('', '--trytond-dir', dest='trytond_dir',
            help='set trytond directory')
    parser.add_option('', '--stdout', action='store_true', dest='stdout',
            help='set output to stdout', default=False)
    parser.add_option('', '--model', dest='model',
            help='Filter only this model')
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose',
            help='Print more verbose log messages', default=False)
    (option, arguments) = parser.parse_args(arguments)

    # Remove first argument because it's application name
    arguments.pop(0)

    if option.trytond_dir:
        directory = os.path.abspath(option.trytond_dir)
    else:
        directory = os.path.abspath(os.path.normpath(os.path.join(os.getcwd(),
                    'trytond')))

    if option.verbose:
        logger.setLevel(logging.DEBUG)
        logging.basicConfig(stream=sys.stderr, level=logging.ERROR)
    else:
        logger.setLevel(logging.INFO)
        logging.basicConfig(stream=sys.stderr, level=logging.ERROR)

    if os.path.isdir(directory):
        sys.path.insert(0, directory)

    if not arguments:
        parser.error("module is required")
    module_name = arguments.pop(0)

    return option, module_name

logger = logging.getLogger('create_xmls')
options, module_name = parse_arguments(sys.argv)

import trytond.tests.test_tryton
from trytond.tests.test_tryton import DB_NAME, USER, CONTEXT
from trytond.transaction import Transaction
from trytond.pool import Pool


def write_view_file(filename, view):
    if options.stdout:
        print view
        return

    if not os.path.exists('view'):
        os.mkdir('view')

    f = open(os.path.join('view', filename), 'w')
    try:
        f.write(view)
    finally:
        f.close()


def generate_tree_view(module_name, model_name, description, inherit_type,
        inherit, fields):
    inherit_tag = ""
    arch = '''\
<?xml version="1.0"?>
<!-- The COPYRIGHT file at the top level of this repository contains the full
     copyright notices and license terms. -->'''

    if inherit_type and inherit_type == 'extends':
        inherit_tag = '\
            <!-- TODO fill "ref" attribute with inherited view of model %s -->\
            <field name="inherit_id" ref=""/>' % inherit
        arch += '<tree position="inside">'
    else:
        arch += '<tree string="%s">' % description
        if inherit:
            arch += '\n<!-- TODO add %s model(s) fields -->' % inherit

    for fieldname in fields:
        arch += '\n    <field name="%s"/>' % fieldname
    arch += '\n</tree>'

    id = model_name.replace('.', '_')
    view_file = "%s_list.xml" % id
    output = """
        <record model="ir.ui.view" id="%s_view_list">
            <field name="model">%s</field>
            <field name="type">tree</field>%s
            <field name="name">%s_list</field>
        </record>""" % (id, model_name, inherit_tag, id)
    write_view_file(view_file, arch)
    return output


def generate_form_view(module_name, model_name, description, inherit_type,
        inherit, fields):

    inherit_tag = ''
    arch = '''\
<?xml version="1.0"?>
<!-- The COPYRIGHT file at the top level of this repository contains the full
     copyright notices and license terms. -->'''

    if inherit_type and inherit_type == 'extends':
        inherit_tag = '\
            <!-- TODO fill "ref" attribute with inherited view of model %s -->\
            <field name="inherit" ref=""/>' % inherit
        arch += '\n<form position="inside">'
    else:
        arch += '\n<form string="%s">' % description
        if inherit:
            arch += (
                '\n <!-- TODO add %s model(s) fields -->'
                % inherit)

    for fieldname in fields:
        arch += '\n    <label name="%s"/>' % fieldname
        arch += '\n    <field name="%s"/>' % fieldname
    arch += '\n</form>'

    id = model_name.replace('.', '_')
    view_file = "%s_form.xml" % id
    output = """
        <record model="ir.ui.view" id="%s_view_form">
            <field name="model">%s</field>
            <field name="type">form</field>%s
            <field name="name">%s_form</field>
        </record>""" % (id, model_name, inherit_tag, id)

    write_view_file(view_file, arch)
    return output


def generate_action(model_name, description):
    id = model_name.replace('.', '_')
    output = """
        <record model="ir.action.act_window" id="act_%s">
            <field name="name">%s</field>
            <field name="res_model">%s</field>
        </record>""" % (id, description, model_name)
    output += """
        <record model="ir.action.act_window.view" id="act_%s_view1">
            <field name="sequence" eval="10"/>
            <field name="view" ref="%s_view_list"/>
            <field name="act_window" ref="act_%s"/>
        </record>""" % (id, id, id)
    output += """
        <record model="ir.action.act_window.view" id="act_%s_view2">
            <field name="sequence" eval="20"/>
            <field name="view" ref="%s_view_form"/>
            <field name="act_window" ref="act_%s"/>
        </record>""" % (id, id, id)
    return output


def generate_users(module_name):
    output = """
        <record model="res.group" id="group_%s_admin">
            <field name="name">%s Administration</field>
        </record>""" % (module_name, module_name.capitalize())
    output += """
        <record model="res.user-res.group" id="user_admin_group_%s_admin">
            <field name="user" ref="res.user_admin"/>
            <field name="group" ref="group_%s_admin"/>
        </record>""" % (module_name, module_name)
    output += """
        <record model="res.user-res.group" id="user_trigger_group_%s_admin">
            <field name="user" ref="res.user_trigger"/>
            <field name="group" ref="group_%s_admin"/>
        </record>""" % (module_name, module_name)
    output += """
        <record model="res.group" id="group_%s">
            <field name="name">%s</field>
        </record>""" % (module_name, module_name.capitalize())
    output += """
        <record model="res.user-res.group" id="user_admin_group_%s">
            <field name="user" ref="res.user_admin"/>
            <field name="group" ref="group_%s"/>
        </record>""" % (module_name, module_name)
    output += """
        <record model="res.user-res.group" id="user_trigger_group_%s">
            <field name="user" ref="res.user_trigger"/>
            <field name="group" ref="group_%s"/>
        </record>""" % (module_name, module_name)
    return output


def generate_access(module_name, model_name):
    id = model_name.replace('.', '_')
    output = """
        <record model="ir.model.access" id="access_%s">
            <field name="model" search="[('model', '=', '%s')]"/>
            <field name="perm_read" eval="True"/>
            <field name="perm_write" eval="False"/>
            <field name="perm_create" eval="False"/>
            <field name="perm_delete" eval="False"/>
        </record>""" % (id, model_name)
    output += """
        <record model="ir.model.access" id="access_%s_admin">
            <field name="model" search="[('model', '=', '%s')]"/>
            <field name="group" ref="group_%s_admin"/>
            <field name="perm_read" eval="True"/>
            <field name="perm_write" eval="True"/>
            <field name="perm_create" eval="True"/>
            <field name="perm_delete" eval="True"/>
        </record>""" % (id, model_name, module_name)
    return output


def generate_menus(module_name, model):
    id = model.model.replace('.', '_')
    output = ('        <menuitem action="act_%s" id="menu_%s" parent="menu_%s"'
        ' sequence="1" name="%s"/>\n' % (id, id, module_name, model.name))
    return output


def create_xml(filename, module_name, model_names):
    output = ''
    output += '<?xml version="1.0" encoding="utf-8"?>\n'
    output += '<tryton>\n'
    output += '    <data>\n'
    menus_output = ''
    output += generate_users(module_name)
    with Transaction().start(DB_NAME, USER, context=CONTEXT):
        pool = Pool()
        Model = pool.get('ir.model')
        models = Model.search([('module', '=', module_name)])
        for model in models:
            if not model.model in model_names:
                continue
            if '-' in model.model:
                continue
            Class = pool.get(model.model)
            fields = Class._fields.keys()
            fields = sorted(list(set(fields) - set(['id', 'create_uid',
                        'create_date', 'write_uid', 'write_date',
                                                    'rec_name'])))
            output += generate_form_view(module_name, model.model,
                model.name, None, None, fields)
            output += generate_tree_view(module_name, model.model,
                model.name, None, None, fields)
            output += generate_action(model.model, model.name)
            output += generate_access(module_name, model.model)
            menus_output += generate_menus(module_name, model)
    output += '\n'
    if menus_output:
        output += '        <!-- Menus -->\n'
        output += ('        <menuitem id="menu_%s" name="%s" sequence="1" />\n'
            % (module_name, module_name.capitalize()))
        output += menus_output
    output += '    </data>\n'
    output += '</tryton>'
    return output


def get_python_files(module_name):
    files = {}
    with Transaction().start(DB_NAME, USER, context=CONTEXT):
        pool = Pool()
        Model = pool.get('ir.model')
        models = Model.search([('module', '=', module_name)])
        for model in models:
            Class = pool.get(model.model)
            module_path = Class.__module__
            # Expected output
            # 'trytond.modules.<module_name>[.<subdir>].<model.model>
            filename = module_path.split('.')[-1]
            if not filename.startswith(module_name):
                filename = module_name + '_' + filename
            files.setdefault(filename, []).append(Class.__name__)
    return files


if __name__ == '__main__':
    warnings.filterwarnings(action='ignore', category=DeprecationWarning)

    logger.info("Generating XMLs for module '%s'" % module_name)
    os.chdir(os.path.join('./modules/', module_name, 'tests'))

    trytond.tests.test_tryton.install_module(module_name)
    files = get_python_files(module_name)
    logger.debug("Python files: %s" % files)
    for filename in files:
        models = files[filename]
        if options.model:
            if options.model in models:
                models = [options.model]
            else:
                models = []
        if not models:
            continue
        output = create_xml(filename + '.xml', module_name, models)
        if options.stdout:
            print output
        else:
            logger.info('\nWriting to %s.xml...\n' % filename)
            f = open(filename + '.xml', 'a')
            try:
                f.write(output)
            finally:
                f.close()
