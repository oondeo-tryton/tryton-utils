#!/usr/bin/python
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
