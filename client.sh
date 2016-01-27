#!/bin/bash
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

pushd `dirname $0` > /dev/null
DIR=`pwd`
popd > /dev/null

rm -rf ~/.config/tryton/3.4/*@*
rm -rf ~/.config/tryton/3.4/known_hosts
rm -rf ~/.config/tryton/3.8/*@*
rm -rf ~/.config/tryton/3.8/known_hosts
rm -rf ~/.config/tryton/3.9/*@*
rm -rf ~/.config/tryton/3.9/known_hosts
rm -rf ~/.config/tryton/4.0/*@*
rm -rf ~/.config/tryton/4.0/known_hosts

DIR="$DIR/tryton"
echo "DIR: $DIR"
if [ ! -d "$DIR" ]; then
    echo "No tryton directory found."
    exit 1
fi

python  $DIR/bin/tryton -d $*
