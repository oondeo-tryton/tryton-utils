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

import sys
import os
import optparse
from proteus import config, Model
import ConfigParser

directory = os.path.abspath(os.path.normpath(os.path.join(os.getcwd(),
                    'trytond')))

if os.path.isdir(directory):
    sys.path.insert(0, directory)


def parse_arguments(arguments):
    parser = optparse.OptionParser(usage='xmls-create.py module [options]')
    parser.add_option('-d', '--database', dest='database',
            help='Database to get modules installed')
    parser.add_option('-c', '--config-file', dest='config',
            help='Config File to update modules')
    (option, arguments) = parser.parse_args(arguments)

    # Remove first argument because it's application name
    arguments.pop(0)

    return option


options = parse_arguments(sys.argv)

config = config.set_trytond(options.database, database_type='postgresql',
    password='admin')

Module = Model.get('ir.module.module')
modules = Module.find([('state', '=', 'installed')])


config = ConfigParser.ConfigParser()
f = open(options.config, 'rw')
config.readfp(f)
f.close()

modules = [module.name for module in modules]

op = config.options('modules')

for module in modules:
    if module in op:
        continue
    print module
    config.set('modules', module, True)

with open(options.config, 'wb') as configfile:
        config.write(configfile)
