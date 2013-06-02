#!/usr/bin/python
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


from proteus import config, Wizard, Model
import os
import sys
from common import Settings
from optparse import OptionParser

dest_path = 'modules/%s/locale'

directory = os.path.abspath(os.path.normpath(os.path.join(os.getcwd(),
                    'trytond')))

if os.path.isdir(directory):
    sys.path.insert(0, directory)


def parse_arguments(arguments):
    usage = 'export_translation.py  -d <database> -m <module> -l <lang>'
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='database')
    parser.add_option('-m', '--module', dest='module')
    parser.add_option('-l', '--lang', dest='lang')

    (option, arguments) = parser.parse_args(arguments)

    settings = Settings()

    if option.database and option.module and option.lang:
        settings.database = option.database
        settings.module = option.module
        settings.lang = option.lang
    else:
        print usage

    return settings

if __name__ == "__main__":

    settings = parse_arguments(sys.argv[1:])

    config.set_trytond(database_type='postgres',
        database_name=settings.database)

    Module = Model.get('ir.module.module')
    if settings.module == 'all':
        modules = Module.find([('state', '=', 'installed')])
    else:
        modules = Module.find([('state', '=', 'installed'),
                ('name', '=', settings.module)])

    print modules
    Lang = Model.get('ir.lang')
    language, = Lang.find([('code', '=', settings.lang)])

    for module in modules:
        translation_export = Wizard('ir.translation.export')
        translation_export.form.language = language
        translation_export.form.module = module
        translation_export.execute('export')
        path = dest_path % module.name
        if not os.path.exists(path):
            continue
        path = path + '/%s.po' % language.code
        if module.name in ('ir', 'webdav', 'res'):
            continue
        f = open(path, 'w')
        try:
            f.write(translation_export.form.file)
        except:
            f.close()
