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
    parser.add_option('-u', '--url', dest='url')
    parser.add_option('-d', '--database', dest='database')
    parser.add_option('-m', '--module', dest='module')
    parser.add_option('-l', '--lang', dest='lang')
    parser.add_option('-p', '--path', dest='path')

    (option, arguments) = parser.parse_args(arguments)

    settings = Settings()

    if (option.database or option.url) and option.module and option.lang:
        settings.database = option.database
        settings.module = option.module
        settings.lang = option.lang
        settings.url = option.url
        settings.path = option.path
    else:
        print usage
    return settings

if __name__ == "__main__":

    settings = parse_arguments(sys.argv[1:])

    if settings.database:
        config.set_trytond(
            database=settings.database)
    else:
        config.set_xmlrpc(settings.url)

    Module = Model.get('ir.module.module')
    if settings.module == 'all':
        modules = Module.find([('state', '=', 'installed')])
    else:
        modules = Module.find([
                ('state', '=', 'installed'),
                ('name', '=', settings.module),
                ])

    Lang = Model.get('ir.lang')
    language, = Lang.find([('code', '=', settings.lang)])

    for module in modules:
        path = settings.path if settings.path else ''
        path = os.path.join(path, dest_path % module.name)
        if not os.path.exists(path):
            path = settings.path if settings.path else ''
            path = os.path.join(path, module.name, 'locale')
            if not os.path.exists(path):
                print 'Path \'%s\' not found.' % path
                continue
        translation_export = Wizard('ir.translation.export')
        translation_export.form.language = language
        translation_export.form.module = module
        translation_export.execute('export')
        path = path + '/%s.po' % language.code
        f = open(path, 'w')
        try:
            f.write(str(translation_export.form.file))
        finally:
            f.close()
        print 'Module \'%s\' exported successfully.' % module.name
