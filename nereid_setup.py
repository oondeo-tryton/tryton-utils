#This file is part of Tryton & Nereid. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import ConfigParser
from setuptools import setup

config = ConfigParser.ConfigParser()
config.readfp(open('trytond_nereid/tryton.cfg'))
info = dict(config.items('tryton'))
for key in ('depends', 'extras_depend', 'xml'):
    if key in info:
        info[key] = info[key].strip().splitlines()
major_version, minor_version, _ = info.get('version', '0.0.1').split('.', 2)
major_version = int(major_version)
minor_version = int(minor_version)

install_requires = [
    'pytz',
    'distribute',
    'flask',
    'wtforms',
    'wtforms-recaptcha',
    'babel',
    'speaklater',
    'Flask-Babel>=0.9',
]

setup(
    name='nereid',
    version=info.get('version'),
    url='http://nereid.openlabs.co.in/docs/',
    license='GPLv3',
    author='Openlabs Technologies & Consulting (P) Limited',
    author_email='info@openlabs.co.in',
    description='Tryton - Web Framework',
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Tryton',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires=install_requires,
    packages=[
        'nereid',
        'nereid.contrib',
        'nereid.tests',
    ],
    package_dir={
        'nereid': 'nereid',
        'nereid.contrib': 'nereid/contrib',
        'nereid.tests': 'nereid/tests',
    },
    zip_safe=False,
    platforms='any',
    test_suite='tests.suite',
    test_loader='trytond.test_loader:Loader',
    tests_require=[
        'trytond_nereid_test >= %s.%s, < %s.%s' %
            (major_version, minor_version, major_version,
                minor_version + 1),
        'mock',
        'pycountry',
        'blinker',
    ],
)
