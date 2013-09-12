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

import os
import sys
import glob
import polib
from optparse import OptionParser
import uuid
from common import Settings, check_output
import re


class ApertiumTranslator:
    def __init__(self, target, source='en'):
        self.source = source
        self.target = target

    def translate(self, text):
        lang = '%s-%s' % (self.source, self.target)
        translation = check_output(['apertium', '-m', lang + ".tmx",
            '-u', lang], text)
        return translation

    def translate_po(self, filename, entries='missing'):
        assert entries in ('missing', 'all'), 'entries parameter must be '\
                '"missing" or "all"'

        po = polib.pofile(filename)
        if entries == 'missing':
            # Includes fuzzy entries
            entries = po.untranslated_entries
        else:
            po
        for entry in po:
            print entry.msgid, entry.msgstr
            entry.msgstr = self.translate(entry.msgid)
            if not 'fuzzy' in entry.flags:
                entry.flags.append('fuzzy')
        po.save()


def parse_arguments(arguments):
    usage = 'translate.py  -m <module> -l <lang>'
    parser = OptionParser(usage=usage)
    parser.add_option('-g', '--generate-tmx', dest='tmx', action="store_true",
        default=False)
    parser.add_option('-m', '--module', dest='module')
    parser.add_option('-l', '--lang', dest='lang')

    (option, arguments) = parser.parse_args(arguments)

    settings = Settings()

    if option.module and option.lang:
        settings.module = option.module
        settings.lang = option.lang
    else:
        print usage

    settings.tmx = False
    if option.tmx:
        settings.tmx = True

    return settings


def make_translation_memory(lang):

    locale_dir = os.path.join(os.getcwd(), 'modules')
    glob_path = os.path.join(locale_dir, '*', 'locale', lang + '.po')

    dst_file = os.path.join('/tmp', str(uuid.uuid4())) + ".po"
    entries = []
    po = polib.POFile()
    po.metadata = {
            'Project-Id-Version': '1.0',
            'Report-Msgid-Bugs-To': 'angel@nan-tic.com',
            'Language-Team': 'English <angel@nan-tic.com.com>',
            'MIME-Version': '1.0',
            'Content-Type': 'text/plain; charset=utf-8',
            'Content-Transfer-Encoding': '8bit',
    }

    for src_file in glob.glob(glob_path):
        pot = polib.pofile(src_file)
        entries += pot.translated_entries()
        entries += pot.fuzzy_entries()
        entries += pot.obsolete_entries()

    terms = []
    for e in entries:
        if e.msgid == e.msgstr:
            continue
        keys = re.findall('\%\(\w+\)s',e.msgid)
        for key in keys:
            po.append(polib.POEntry(
                msgid=key,
                msgstr=key))

        term = (e.msgid, e.msgstr)
        if term not in terms:
            terms.append(term)

        if e.flags:
            e.flags.remove('fuzzy')
        po.append(e)
    po.save(dst_file)

    check_output(['po2tmx', '-l', lang[:2], '-i', dst_file, '-o',
         'en-%s.tmx' % lang[:2]])

if __name__ == "__main__":

    settings = parse_arguments(sys.argv[1:])

    if settings.tmx:
        print "* Generating tmx memmory file..."
        make_translation_memory(settings.lang)
        print "* Finish tmx"

    print "* Start translation module:", settings.module
    locale_dir = os.path.join(os.getcwd(), 'modules', settings.module,
        'locale')
    locale_file = os.path.join(locale_dir, settings.lang + '.po')
    ap = ApertiumTranslator(settings.lang.split('_')[0])
    ap.translate_po(locale_file)
    print "* Translation finished"
    print "* Please, Remember to upadte to module to update terms"
