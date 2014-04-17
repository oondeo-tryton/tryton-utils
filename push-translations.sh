#!/bin/bash

user=$1
lang=$2
force=$3

if [[ -z "$1" || -z "$2" ]]; then
    echo "Usage: $0 user lang [action]"
    echo
    echo "If action is empty it will just print the commit and push commands"
    echo "it would execute."
    echo "If action is 'commit' it will make the commit."
    echo "If action is 'push' it will push the commits to the server."
    exit 0
fi

pushd trytond || exit 1
for directory in $(hg nstatus | grep "\[" | sed 's/\[//' | sed 's/\]//'); do
    if [[ "$directory" == "." ]]; then
        continue
    fi
    pushd $directory || exit 1
    module=$(basename $directory)
    hg add locale/${lang}.po
    if [[ "$force" == "commit" ]]; then
        hg commit -m "Update ${lang} translation"
    elif [[ "$force" == "push" ]]; then
        hg push ssh://$user@hg.tryton.org///home/hg/modules/$module
    else
        echo "hg commit -m 'Update ${lang} translation'"
        echo "hg push ssh://$user@hg.tryton.org///home/hg/modules/$module"
    fi
    popd
done

hg nstatus
popd
