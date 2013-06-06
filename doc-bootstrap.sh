#!/bin/bash

echo $(pwd)
pushd buildout
./build/bin/buildout -c userdoc.cfg
./create-doc-symlinks.sh
popd
pushd userdoc
make
popd


