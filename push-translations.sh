#!/bin/bash

lang=ca_ES
user=albertca

pushd trytond || exit 1
for module in $(hg nstatus | grep "\[" | sed 's/\[//' | sed 's/\]//'); do
    if [[ "$module" == "." ]]; then
        continue
    fi
    pushd $dir || exit 1
    hg add locale/${lang}.po
    echo hg commit -m "Update ${lang} translation"
    #hg commit -m "Update ${lang} translation"
    echo "hg push ssh://$user@hg.tryton.org///home/hg/modules/$module"
    #hg push ssh://$user@hg.tryton.org///home/hg/modules/$module
    popd
done

hg nstatus
popd
