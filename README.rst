--------------
create-xmls.py
--------------

This script creates views, users, permissions, menu items and actions. Currently
they are created in the tests/ directory of the module.

Usage::

    ./create-xmls.py module_name


------------
translate.py
------------

Translate module using apertium with the possibility to use a specific
dictionary file, genereted by this script. [http://www.apertium.org/]

To use specific dictionary, you need to generate tmx file, use **-g** option
to do it.

 ::
    ./utils/translate.py -g -l ca_ES -m <module-name>
This command, first generate en-ca.tmx file and then translate all terms of
<module-name>.


----------------------
export_translations.py
----------------------

Export especific language from tryton module using proteus.

 ::

    ./utils/export_translations -d <database> -m <module> -l <language>


---------------------
check_translations.py
---------------------

Some statistics from po file, like translation percent, fuzzy and untranslated
terms

 ::

    ./utils/check_translations -m <module> -l <language>


-----------------
create-project.sh
-----------------

Creates a new tryton project based on NaN·tic's buildout repository::

    ./create-project.sh <project_name> <version>

Version is currently required although it is not used yet.


----------------
doc-bootstrap.sh
----------------
First you need to install dependencies,  download repositories

* hg clone https://bitbucket.org/nantic/sphinxcontrib-inheritance
* hg clone https://bitbucket.org/nantic/trydoc" 

and as root:

cd sphinxcontrib-inheritance  && python setup.py install
cd trydoc &&  python setup.py install

and as user:

./utils/doc-bootstrap.sh

---------------------
doc-update-modules.py
---------------------

To update modules used in documentation.

./utils/doc-update-modules.py -d <database> -c <config-file>

Rembember to execute doc-bootstrap.sh to generate documentation again.




