#!/usr/bin/env python
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


import ConfigParser
import optparse
import os
import signal
import socket
import subprocess
import sys
import time
import re
import shutil
import datetime
import glob
import socket

# krestart is the same as restart but will execute kill after
# stop() and before the next start()
ACTIONS = ('start', 'stop', 'restart', 'startserver', 'stopserver',
    'restartserver', 'startweb', 'stopweb', 'restartweb', 'status',
    'status_web', 'kill', 'krestart', 'config', 'config_web', 'ps', 'db')

# Start Printing Tables
# http://ginstrom.com/scribbles/2007/09/04/pretty-printing-a-table-in-python/

def format_num(num):
    """Format a number according to given places.
        Adds commas, etc. Will truncate floats into ints!"""

    try:
        inum = int(num)
        return locale.format("%.*f", (0, inum), True)

    except (ValueError, TypeError):
        return str(num)

def get_max_width(table, index):
    """Get the maximum width of the given column index"""
    return max([len(format_num(row[index])) for row in table])

def pprint_table(table):
    """
    Prints out a table of data, padded for alignment
    @param table: The table to print. A list of lists.
    Each row must have the same number of columns.
    """
    col_paddings = []

    for i in range(len(table[0])):
        col_paddings.append(get_max_width(table, i))

    for row in table:
        # left col
        print row[0].ljust(col_paddings[0] + 1),
        # rest of the cols
        for i in range(1, len(row)):
            col = format_num(row[i]).rjust(col_paddings[i] + 2)
            print col,
        print

# End Printing Tables

def transpose(data):
    if not data:
        return data
    return [[row[i] for row in data] for i in xrange(len(data[0]))]

def backup_and_remove(filename):
    # Remove old backups
    for f in glob.glob('%s.*' % filename):
        os.remove(f)
    timestamp = datetime.datetime.today().strftime('%Y-%m-%d_%H:%M:%S')
    destfile = '%s.%s' % (filename, timestamp)
    if os.path.exists(filename):
        shutil.move(filename, destfile)
    return destfile

def check_output(*args):
    process = subprocess.Popen(args, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    process.wait()
    data = process.stdout.read()
    return data

def get_fqdn():
    #socket.getfqdn()
    data = check_output('hostname','--fqdn')
    data = data.strip('\n').strip('\r').strip()
    if not data:
        # In some hosts we may get an error message on stderr with
        # 'No such host'.
        # if using --fqdn parameter. In this case, try to run hostname
        # without parameters.
        data = check_output('hostname')
        data = data.strip('\n').strip('\r').strip()
    return data

def get_database_list():
    databases = []
    # Only works if using standard port
    lines = check_output('psql', '-l', '-t')
    for line in lines.split('\n'):
        fields = line.split('|')
        db = fields[0].strip()
        if db:
            databases.append(db)
    return databases

def processes(filter=None):
    """
    Lists all process containing 'filter' in its command line.
    """
    # Put the import in the function so the package is not required.
    import psutil
    import getpass

    # TODO: Filter by user
    me = getpass.getuser()
    processes = []
    for process in psutil.get_process_list():
        try:
            cmdline = ' '.join(process.cmdline)
        except psutil.error.NoSuchProcess:
            # The process may disappear in the middle of the loop
            # so simply ignore it.
            pass
        if filter and filter in cmdline:
            processes.append(process)
    return processes

def kill_process(filter, name):
    """
    Kills all process containing 'filter' in the command line.
    """
    # Put the import in the function so the package is not required.
    import psutil

    for process in processes(filter):
        pid = process.pid
        try:
            os.kill(pid, 15)
        except OSError:
            continue

        time.sleep(0.3)
        if psutil.pid_exists(pid):
            os.kill(pid, 9)
            time.sleep(0.3)
            if psutil.pid_exists(pid):
                print 'Could not kill %s process %d.' % (name, pid)
            else:
                print 'Killed %s process %d.' % (name, pid)
        else:
            print 'Terminated %s process %d.' % (name, pid)

def kill():
    """
    Kills all trytond and JasperServer processes
    """
    kill_process('trytond', 'trytond')
    kill_process('pen -p', 'pen')
    kill_process('java -Djava.awt.headless=true '
        'com.nantic.jasperreports.JasperServer', 'jasper')

def ps():
    for process in processes(filter='trytond'):
        print '%d %s' % (
            process.pid,
            ' '.join(process.cmdline)
           )

def db():
    import psycopg2
    import psycopg2.extras
    database = psycopg2.connect("dbname=%s"%('template1'))
    cursor = database.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Databases
    cursor.execute('SELECT datname FROM pg_database')
    records = cursor.fetchall()
    databases = [x['datname'] for x in records]

    data = []
    data.append(databases[:])

    sizes = []
    # Size
    for database in databases:
        cursor.execute("SELECT pg_size_pretty(pg_database_size('%s')) AS size"
            % database);
        size = cursor.fetchone()['size']
        sizes.append(size)
        #print "Database: %s, Size: %s" % (database, size)
    data.append(sizes)

    pprint_table(transpose(data))

    # Activity
    #print "Activity:"
    #cursor.execute('SELECT * FROM pg_stat_activity')
    #print dir(cursor)
    #records = cursor.fetchall()
    #for record in records:
    #    line = []
    #    for field in record.keys():
    #        line.append('%s=%s' % (field, record[field]))
    #    print ' '.join(line)

def fork_and_call(call, pidfile=None, logfile=None, cwd=None):
    # do the UNIX double-fork magic, see Stevens' "Advanced
    # Programming in the UNIX Environment" for details (ISBN 0201563177)
    try:
        pid = os.fork()
        if pid > 0:
            # parent process, return and keep running
            return
    except OSError, e:
        print >>sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror)
        sys.exit(1)

    os.setsid()

    # do second fork
    try:
        pid = os.fork()
        if pid > 0:
            # exit from second parent
            sys.exit(0)
    except OSError, e:
        print >>sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror)
        sys.exit(1)

    if logfile:
        output = open(logfile, 'a')
    else:
        output = None
    # do stuff
    process = subprocess.Popen(call, stdout=output, stderr=output, cwd=cwd)

    if pidfile:
        file = open(pidfile, 'w')
        file.write(str(process.pid))
        file.close()

    # all done
    os._exit(os.EX_OK)

class Settings(dict):
    def __init__(self, *args, **kw):
        super(Settings, self).__init__(*args, **kw)
        self.__dict__ = self

def parse_arguments(arguments, root):
    parser = optparse.OptionParser(usage='server.py [options] start|stop|'
        'restart|startserver|stopserver|restartserver|startweb|stopweb|'
        'restartweb|status|status_web|kill|krestart|config|config_web|'
        'ps|db [database [-- parameters]]')
    parser.add_option('', '--config', dest='config',
        help='(it will search: server-config_name.cfg')
    parser.add_option('', '--config-file', dest='config_file', help='')
    parser.add_option('', '--debug', action='store_true', help='')
    parser.add_option('', '--debug-rpc', action='store_true', help='')
    parser.add_option('', '--no-tail', action='store_true', help='')
    parser.add_option('', '--server-help', action='store_true', help='')
    parser.add_option('', '--verbose', action='store_true', help='')
    parser.add_option('', '--clear', action='store_true', help='')
    #parser.add_option('', '--clean-server-log', action='store_true', help='')
    #parser.add_option('', '--clean-web-server-log', action='store_true',
    #    help='')
    (option, arguments) = parser.parse_args(arguments)
    # Remove first argument because it's application name
    arguments.pop(0)

    settings = Settings()

    if option.verbose is None:
        settings.verbose = False
    else:
        settings.verbose = option.verbose

    if option.config and option.config_file:
        print '--config and --config-file options are mutually exclusive.'
        sys.exit(1)

    settings.clear = option.clear

    fqdn = get_fqdn()
    if option.config:
        filename = 'server-%s.cfg' % option.config
        settings.config = os.path.join(root, filename)
    elif option.config_file:
        settings.config = os.path.join(root, option.config_file)
    else:
        settings.config = os.path.join(root, 'server-%s.cfg' % fqdn)

    settings.tail = not option.no_tail

    settings.debug = option.debug
    settings.debug_rpc = option.debug_rpc

    if settings.verbose:
        print "Configuration file: %s" % settings.config

    settings.config_web = os.path.join(root, 'web-%s.cfg' % fqdn)

    if not arguments:
        print 'One action is required.'
        sys.exit(1)

    settings.action = arguments.pop(0)
    if not settings.action in ACTIONS:
        print 'Action must be one of %s.' % ','.join([x for x in ACTIONS])
        sys.exit(1)

    settings.database = None

    if arguments:
        value = arguments.pop(0)
        settings.database = value

    if settings.database and settings.database == '-':
        project = os.path.split(root)[-1]
        # Search all databases that have 'current project' in the name and
        # sort them
        databases = sorted([x for x in get_database_list() if project in x])
        if databases:
            settings.database = databases[-1]
        else:
            settings.database = None

    settings.pidfile = os.path.join(root, 'trytond.pid')
    settings.pidfile_web = os.path.join(root, 'openerp-web.pid')
    settings.pidfile_jasper = os.path.join(root, 'tryton-jasper.pid')
    settings.logfile = os.path.join(root, 'server.log')
    settings.logfile_web = os.path.join(root, 'web_server.log')

    settings.extra_arguments = arguments[:]

    return settings

# Returna a list of NUM free ports to use
def take_free_port(num=1):
    ports = []
    n = 0
    while n < num:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("",0))
        ports.append(s.getsockname()[1])
        s.close()
        n += 1
    return ports

def load_config(filename, settings, pensettings=None):
    values = {}

    if not os.path.isfile(filename):
        return values

    parser = ConfigParser.ConfigParser()
    parser.read([filename])
    for section in parser.sections():
        for (name, value) in parser.items(section):
            values['%s.%s' % (section, name)] = value

    if values.get('options.server_pidfile'):
        settings.pidfile = values.get('options.server_pidfile')

    if values.get('options.server_logfile'):
        settings.logfile = values.get('options.server_logfile')

    if values.get('options.jasperpid'):
        settings.pidfile_jasper = values.get('options.jasperpid')

    if pensettings is None:
        return values

    # Take the PEN values, if exist, from the penoption
    # config section of the multiprocess
    if values.get('penoptions.multi_port', 'False') == 'False':
        pensettings.multi_port = False
    else:
        pensettings.multi_port = True
    if pensettings.multi_port:
        pensettings.filename = filename
        # Add one server more for the esclusive cron server
        pensettings.num_servers = int(values.get('penoptions.num_servers')) + 1
        pensettings.max_con = values.get('penoptions.max_con')
        if values.get('penoptions.create_cron', 'False') == 'False':
            pensettings.create_cron = False
        else:
            pensettings.create_cron = True
        if values.get('penoptions.cron_alone', 'False') == 'False':
            pensettings.cron_alone = False
        else:
            pensettings.cron_alone = True
        if values.get('penoptions.round_robin', 'False') == 'False':
            pensettings.round_robin = ""
        else:
            pensettings.round_robin = "-r"
        pensettings.penconfs = {}
        host = values.get('penoptions.host')
        for port in [values.get('options.port') or
                values.get('options.xmlrpc_port'),
                values.get('options.netport') or
                values.get('options.netrpc_port'),
                values.get('options.pyroport'),
                values.get('options.xmlrpcs_port'),
                values.get('options.ftp_server_port')]:
            if port:
                penconf = {
                    'pidfile': "%s.%s" % (values.get('penoptions.pidfile'),
                        port),
                    'ctrl': "%s:%s" % (host, take_free_port()[0]),
                    'host': host,
                    'ports': take_free_port(pensettings.num_servers),
                    }
                pensettings.penconfs[port] = Settings(penconf)
    return values

def find_directory(root, directories):
    for directory in directories:
        path = os.path.join(root, directory)
        if os.path.isdir(path):
            return path
    return None

def start(settings):
    """
    Starts OpenERP server.
    """

    server_directories = [
        'trytond',
        ]
    path = find_directory(settings.root, server_directories)
    if not path:
        print 'Could not find server directory.'
        sys.exit(1)

    # Set executable name
    call = ['python', '-u', os.path.join(path, 'bin', 'trytond')]

    if os.path.exists(settings.config):
        call += ['-c', settings.config]
    else:
        # If configuration file does not exist try to start the server anyway
        print 'Configuration file not found: %s' % settings.config

    if settings.database:
        call += ['--database', settings.database]
    if settings.debug:
        call += ['--log-level', 'debug']
    elif settings.debug_rpc:
        call += ['--log-level', 'debug_rpc']

    call += settings.extra_arguments

    if settings.verbose:
        print "Calling '%s'" % ' '.join(call)

    # Create pidfile ourselves because if OpenERP server crashes on start it may
    # not have created the file yet while keeping the process running.
    fork_and_call(call, settings.pidfile, settings.logfile)

def start_web(settings):
    """
    Starts OpenERP's web client using settings.config_web filename.
    """
    # Only start web server if configuration file exists
    if not os.path.exists(settings.config_web):
        return

    server_directories = [
        'nereid',
        ]
    path = find_directory(settings.root, server_directories)
    if not path:
        print 'Could not find server directory.'
        sys.exit(1)

    # Set executable name
    call = [os.path.join(path, 'openerp-web.py')]

    call += ['-c', settings.config_web]

    if settings.verbose:
        print "Calling '%s'" % ' '.join(call)

    #output = open(settings.logfile_web, 'a')

    fork_and_call(call, settings.pidfile_web, settings.logfile_web)

def stop(pidfile, warning=True):
    """
    Stops OpenERP's application server or PEN servers.

    If warning=True it will show a message to the user when pid file does
    not exist.
    """
    if not pidfile:
        return
    if not os.path.exists(pidfile):
        if warning:
            print 'Pid file %s does not exist.' % pidfile
        return
    pid = open(pidfile, 'r').read()
    try:
        pid = int(pid)
    except ValueError:
        print "Invalid pid number: %s" % pid
        return
    try:
        os.kill(pid, 9)
    except OSError:
        print "Could not kill process with pid %d. Probably it's no longer running." % pid
    finally:
        try:
            os.remove(pidfile)
        except OSError:
            print "Error trying to remove pidfile %s" % pidfile

def tail(filename):
    file = open(filename, 'r')
    try:
        while 1:
            where = file.tell()
            line = file.readline()
            if not line:
                time.sleep(1)
                file.seek(where)
            else:
                print line,
    except KeyboardInterrupt:
        print "Server monitoring interrupted. Server will continue working..."
    finally:
        file.close()

def create_config_file(pensettings, config, num_file=0, context={}):
    cronfile = context.get('cronfile')
    webfile = context.get('webfile')
    configfile_name = "%s%s" % (pensettings.filename, num_file)
    configfile = open(configfile_name, 'w')
    configfile.write("[options]\n")
    for k, v in config.iteritems():
        kvals = k.partition(".")
        if kvals[0] == "options":
            if v in pensettings.penconfs:
                configfile.write("%s = %s\n" % (kvals[2],
                        pensettings.penconfs[v].ports[num_file]))
            elif not webfile and (kvals[2] == "config_web" or
                kvals[2] == "server_web_logfile" or
                kvals[2] == "server_start_web_pidfile"):
                configfile.write("%s =\n" % kvals[2])
            elif (kvals[2] == "server_logfile" or kvals[2] == "server_pidfile"
                or kvals[2] == "server_start_pidfile"):
                configfile.write("%s = %s%s\n" % (kvals[2], v, num_file))
            else:
                configfile.write("%s = %s\n" % (kvals[2], v))
    if cronfile:
        configfile.write("cron = True")
    else:
        configfile.write("cron = False")
    configfile.close()
    return configfile_name

def create_multi_config_files(config, pensettings, settings):
    # Prepare the differents config files as many as ports
    # are deffined for the main config file
    multi_settings = [None] * pensettings.num_servers
    num_file = 0
    # Create file that contain cron config call
    multi_settings[num_file] = Settings(settings)
    multi_settings[num_file].config = create_config_file(pensettings, config,
            num_file, {'cronfile': pensettings.create_cron, 'webfile': False})

    num_file += 1
    while num_file < (pensettings.num_servers - 1):
        multi_settings[num_file] = Settings(settings)
        multi_settings[num_file].config = create_config_file(pensettings,
                config, num_file, {'cronfile': False, 'webfile': False})
        num_file += 1

    # Create file that contain web config
    multi_settings[num_file] = Settings(settings)
    multi_settings[num_file].config = create_config_file(pensettings, config,
            num_file, {'cronfile': False, 'webfile': True})

    # reedit the differents settings needed
    num_file = 0
    while num_file < pensettings.num_servers:
        config = load_config(multi_settings[num_file].config,
            multi_settings[num_file])
        num_file += 1

    return multi_settings

def start_multi(pensettings, multi_settings):
    for settings in multi_settings:
        start(settings)
    for penport, penvals in pensettings.penconfs.iteritems():
        call = ["/usr/bin/pen", pensettings.round_robin,  "-p", penvals.pidfile,
                "-C", penvals.ctrl, penport]
        if pensettings.cron_alone:
            penvals.ports.pop(0)
        call.extend(["%s:%s:%s" % (penvals.host, port, pensettings.max_con) for port in penvals.ports])
        subprocess.call(call)

def stop_multi(pensettings, multi_settings):
    for penport, penvals in pensettings.penconfs.iteritems():
        stop(penvals.pidfile)
    for settings in multi_settings:
        stop(settings.pidfile)
        # try:
        #     os.remove(settings.config)
        # except OSError:
        #     print "Error trying to remove config file: %s" % settings.config

root = os.path.dirname(sys.argv[0])
# If the path contains 'utils', it's probably being executed from the
# clone of the utils repository in the project which is expected to be in
# project/utils. So simply add '..' to get: project/utils/.. which is
# where all directories should be found.
if 'utils' in root:
    root = os.path.join(root, '..')
root = os.path.abspath(root)

settings = parse_arguments(sys.argv, root)
settings.root = root

if settings.verbose:
    print "Root: %s" % root

pensettings = Settings()
pensettings.multi_port = False

config = load_config(settings.config, settings, pensettings)

if settings.action == 'ps':
    ps()

if settings.action == 'db':
    db()

if settings.action == 'config':
    try:
        print open(settings.config, 'r').read()
        sys.exit(0)
    except IOError:
        sys.exit(255)

if settings.action == 'config_web':
    try:
        print open(settings.config_web, 'r').read()
        sys.exit(0)
    except IOError:
        sys.exit(255)

if 'multi_port' in pensettings and pensettings.multi_port:
    multi_settings = create_multi_config_files(config, pensettings, settings)

if settings.action in ('start', 'restart', 'krestart'):
    if os.path.exists('doc/user'):
        fork_and_call(['make', 'html'], cwd='doc/user', logfile='doc.log')
    else:
        print "No user documentation available."

if settings.action in ('stop', 'restart', 'krestart', 'stopserver',
        'restartserver', 'stopweb', 'restartweb'):
    if settings.action in ('stop', 'restart', 'krestart', 'stopserver',
            'restartserver'):
        if pensettings.multi_port:
            stop_multi(pensettings, multi_settings)
        else:
            stop(settings.pidfile)
    if settings.action in ('stop', 'restart', 'krestart', 'stopweb',
            'restartweb'):
        stop(settings.pidfile_web, warning=False)
    stop(settings.pidfile_jasper, warning=False)

if settings.action in ('kill', 'krestart'):
    kill()

if settings.action in ('start', 'restart', 'krestart', 'startserver',
        'restartserver', 'startweb', 'restartweb'):
    if settings.action in ('start', 'restart', 'krestart', 'startserver',
            'restartserver'):
        if pensettings.multi_port:
            for settings in multi_settings:
                backup_and_remove(settings.logfile)
        else:
            backup_and_remove(settings.logfile)
    if settings.action in ('start', 'restart', 'krestart', 'startweb',
            'restartweb'):
        backup_and_remove(settings.logfile_web)

if settings.action in ('start', 'restart', 'krestart', 'startserver',
        'restartserver', 'startweb', 'restartweb'):
    if settings.action in ('start', 'restart', 'krestart', 'startserver',
            'restartserver'):
        if pensettings.multi_port:
            start_multi(pensettings, multi_settings)
        else:
            start(settings)
    if settings.action in ('start', 'restart', 'krestart', 'startweb',
            'restartweb'):
        start_web(settings)

    if settings.tail:
        # Ensure server.log has been created before executing 'tail'
        time.sleep(1)
        if pensettings.multi_port:
            tail(multi_settings[0].logfile)
        else:
            tail(settings.logfile)

if settings.action == 'status':
    if pensettings.multi_port:
        tail(multi_settings[0].logfile)
    else:
        tail(settings.logfile)

if settings.action == 'status_web':
    tail(settings.logfile_web)
