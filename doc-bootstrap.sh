#!/bin/bash

echo $(pwd)
echo "Please install the last version of trydoc and sphinxcontrib-inheritance"
echo "hg clone https://bitbucket.org/nantic/sphinxcontrib-inheritance"
echo "hg clone https://bitbucket.org/nantic/trydoc" 

read
pushd buildout
./build/bin/buildout -c userdoc.cfg
./create-doc-symlinks.sh
popd
pushd userdoc
if [ ! -f ./userdoc/modules.cfg ]
then
    touch ./userdoc/modules.cfg
    echo [modules] >> ./userdoc/modules.cfg
fi

make
popd


