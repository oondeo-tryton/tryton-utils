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


echo "server.py"
diff ../server.py server.py
if [[ -f ../server.py ]]; then
    mv ../server.py /tmp
fi
ln -s utils/server.py ..

echo "client.sh"
diff ../client.sh client.sh
if [[ -f ../client.sh ]]; then
    mv ../client.sh /tmp
fi
ln -s utils/client.sh ..
