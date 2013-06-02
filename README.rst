--------------
xmls-create.py
--------------

This script creates views, users, permissions, menu items, actions.

Usage:

python xmls-create.py module_name  


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
terms.

 ::

    ./utils/check_translations -m <module> -l <language>





