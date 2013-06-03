#!/bin/bash

if [ -d "tryton" ]; then
    DIR="tryton"
else
    echo "No tryton directory found."
    exit 1
fi

python  ./$DIR/bin/tryton $*
