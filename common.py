#!/usr/bin/python
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

import subprocess

class Settings(dict):
    def __init__(self, *args, **kw):
        super(Settings, self).__init__(*args, **kw)
        self.__dict__ = self

def check_output(app, stdin=''):
    process = subprocess.Popen(app, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    stdout, stderr = process.communicate(stdin.encode('utf-8'))
    process.wait()
    return unicode(stdout, 'utf-8')
