#!/usr/bin/python

from proteus import config, Wizard, Model
import os

dest_path = 'modules/%s/locale'
database_name = 'tryton'
language_code = 'ca_ES'

config.set_trytond(database_type='postgres', database_name=database_name)

Module = Model.get('ir.module.module')
modules = Module.find([('state', '=', 'installed')])
Lang = Model.get('ir.lang')
language, = Lang.find([('code', '=', language_code)])

for module in modules:
    translation_export = Wizard('ir.translation.export')
    translation_export.form.language = language
    translation_export.form.module = module
    translation_export.execute('export')
    path = dest_path % module.name
    if not os.path.exists(path):
        continue
    path = path + '/%s.po' % catalan.code
    if module.name in ('ir', 'webdav', 'res'):
        continue
    f = open(path, 'w')
    try:
        f.write(translation_export.form.file)
    except:
        f.close()
