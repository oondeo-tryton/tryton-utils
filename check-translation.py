#!/usr/bin/python

import os
import sys
import glob
import polib
from optparse import OptionParser
import uuid
from common import Settings, check_output


def parse_arguments(arguments):
    usage = 'check-translation.py -m <module> -l <lang>'
    parser = OptionParser(usage=usage)
    parser.add_option('-m', '--module', dest='module')
    parser.add_option('-l', '--lang', dest='lang')

    (option, arguments) = parser.parse_args(arguments)

    settings = Settings()

    if option.module and option.lang:
        settings.module = option.module
        settings.lang = option.lang
    else:
        print usage
    return settings

def check_translation(file_name):

    po = polib.POFile(file_name)
    print "* Percentage Translated: ", po.percent_translated()
    untranslated = po.untranslated_entries()
    if untranslated:
        print "* Untranslated terms ------------------"
        for entry in untranslated:
            print "   ", entry.msgid

    fuzzy = po.fuzzy_entries()
    if fuzzy:
        print "* Fuzzy terms ------------------"
        for entry in fuzzy:
            print "   ", entry.msgid

if __name__ == "__main__":

    settings = parse_arguments(sys.argv[1:])

    print "* Check translation for module:", settings.module
    locale_dir = os.path.join(os.getcwd(), 'modules', settings.module,
        'locale')
    locale_file = os.path.join(locale_dir, settings.lang + '.po')
    print "* File:", locale_file
    check_translation(locale_file)

