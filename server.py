#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
# Copyright (C) 2015 NaN·tic
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
import socket
import subprocess
import sys
import time
import locale
import signal
import glob
import datetime
import shutil
from urlparse import urlparse
import re
try:
    from jinja2 import Template as Jinja2Template
    jinja2_loaded = True
except ImportError:
    jinja2_loaded = False


# krestart is the same as restart but will execute kill after
# stop() and before the next start()
ACTIONS = ('start', 'stop', 'restart', 'status', 'kill', 'krestart', 'config',
    'ps', 'db', 'top', 'backtrace', 'console')

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

def transpose(data):
    if not data:
        return data
    return [[row[i] for row in data] for i in xrange(len(data[0]))]

def backup_and_remove(filename):
    # Remove old backups
    # The last 3 files are kept so we'll have the new one (.log$), the new old
    # and the other 3 that already existed
    to_remove = sorted(glob.glob('%s.*' % filename))
    to_remove = to_remove[:-3]
    for f in to_remove:
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
    #import getpass

    # TODO: Filter by user
    #me = getpass.getuser()
    processes = []
    for process in psutil.process_iter():
        try:
            if isinstance(process.cmdline, (tuple, list)):
                cmdline = process.cmdline
            else:
                try:
                    cmdline = process.cmdline()
                except psutil.AccessDenied:
                    continue
            cmdline = ' '.join(cmdline)
        except psutil.NoSuchProcess:
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
    kill_process('nginx -c', 'nginx')
    kill_process('java -Djava.awt.headless=true '
        'com.nantic.jasperreports.JasperServer', 'jasper')

def ps():
    for process in processes(filter='trytond'):
        print '%d %s' % (
            process.pid,
            ' '.join(process.cmdline)
           )

def console(settings):
    from IPython.terminal.embed import InteractiveShellEmbed
    if not settings.database:
        print 'No database specified.'
        sys.exit(1)

    uri = 'postgresql:///%s' % settings.database

    def models(filters):
        search = filters.replace(' ', '%')
        M = Model.get('ir.model')
        models = M.find(['model', 'ilike', '%' + search + '%'])
        for model in models:
            print '%s  --  %s' % (model.model, model.name)

    print "Launching tryton>proteus console on %s..." % uri
    banner = ('Proteus Help:\n'
        "Classes\t\t-> Model, Wizard & Report\n"
        "Push button\t-> record.click('confirm')\n"
         "Show models\t-> %models stock shipment\n")

    ipshell = InteractiveShellEmbed(banner2=banner)
    ipshell.register_magic_function(models)

    # Imports and config setup to be used in Interactive Shell
    from proteus import config, Model, Wizard, Report
    # Just use Wizard and Report to avoid pyflakes warnings
    Wizard
    Report
    config.set_trytond(uri)

    ipshell()


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

def parse_arguments(arguments, root, extra=True):
    parser = optparse.OptionParser(usage='server.py [options] start|stop|'
        'restart|status|kill|krestart|config|ps|db|top|console '
        '[database [-- parameters]]')
    parser.add_option('', '--config', dest='config',
        help='(it will search: server-config_name.cfg')
    parser.add_option('', '--config-file', dest='config_file', help='')
    parser.add_option('', '--no-tail', action='store_true', help='')
    parser.add_option('', '--server-help', action='store_true', help='')
    parser.add_option('', '--verbose', action='store_true', help='This verbose'
        ' is only for the server.py execution, it is not the tryton verbose, '
        'it has to be defined in the server config file.')
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

    fqdn = get_fqdn()
    if option.config:
        filename = 'server-%s.cfg' % option.config
        settings.config = os.path.join(root, filename)
    elif option.config_file:
        settings.config = os.path.join(root, option.config_file)
    else:
        instance = os.path.basename(os.path.realpath(os.path.join(
                    os.path.dirname(os.path.realpath(__file__)), '..')))
        paths = (
            '/etc/trytond/%s.conf' % instance,
            os.path.join(root, 'server-%s.cfg' % fqdn),
            os.path.join(root, 'trytond.conf'),
            os.environ.get('TRYTOND_CONFIG'),
            )
        for settings.config in paths:
            if settings.verbose:
                print 'Checking %s...' % settings.config
            if os.path.exists(settings.config):
                break

    settings.tail = not option.no_tail

    if settings.verbose:
        print "Configuration file: %s" % settings.config

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

    settings.pidfiles = [os.path.join(root, 'trytond.pid')]
    settings.pidfile_jasper = os.path.join(root, 'jasper.pid')
    settings.logfile = os.path.join(root, 'server.log')

    settings.extra_arguments = []
    if extra:
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

def load_config(filename, settings):
    values = {}

    if not os.path.isfile(filename):
        return values

    parser = ConfigParser.ConfigParser()
    parser.read([filename])
    for section in parser.sections():
        for (name, value) in parser.items(section):
            values['%s.%s' % (section, name)] = value

    if 'optional.dev' in values and values['optional.dev'].lower() != 'false':
        settings.dev = '--dev'
    else:
        settings.dev = False

    if ('optional.cron' in values and
        values['optional.cron'].lower() != 'false'):
        settings.cron = '--cron'
    else:
        settings.cron = False

    if ('optional.verbose' in values and
        values['optional.verbose'].lower() != 'false'):
        settings.verb = '--verbose'
    else:
        settings.verb = False

    if 'optional.logconf' in values:
        settings.logconf = values.get('optional.logconf')
        newparser = ConfigParser.ConfigParser()
        newparser.read(settings.logconf)
        args = newparser.get('handler_trfhand', 'args')
        settings.logfile = re.match(
            "\('([0-9a-zA-z/.\-_]+)',.*$", args).group(1)
    else:
        settings.logconf = False

    if 'optional.nginx_tmpl' in values:
        settings.nginx_tmpl = values.get('optional.nginx_tmpl')

    if values.get('database.uri') and not settings.database:
        parse = urlparse(values.get('database.uri'))
        settings.database = parse.path[1:]

    if values.get('optional.pidfile'):
        settings.pidfiles = [values.get('optional.pidfile')]

    if values.get('jasper.pid'):
        settings.pidfile_jasper = values.get('jasper.pid')

    if (values.get('optional.workers', 'False') != 'False' and
        values.get('optional.nginx_tmpl', 'False') != 'False'):

        settings.doc_port = values.get('optional.doc_port')
        try:
            workers = int(values['optional.workers'])
        except:
            print "Invalid workers value. It has to be a number or 'False'."
            sys.exit(1)

        (settings.config_multiserver, settings.config_nginx) = (
            prepare_multiprocess(parser, values, filename, workers))

        if not values.get('optional.pidfile'):
            print "[MULTIPROCESS] Pid file path definition is needed."
            sys.exit(1)
        settings.pidfiles = []
        w = 1
        while w <= workers:
            settings.pidfiles.append(
                "%s.%s" % (values.get('optional.pidfile'), w))
            w += 1
    else:
        settings.config_multiserver = False
        settings.config_nginx = False
        settings.doc_port = False

    return values

def prepare_multiprocess(parser, values, filename, workers):
    filename = os.path.basename(filename)
    ports = take_free_port(workers * 3)
    used_ports = {}
    configfile_names = []
    nginx_files = []
    w = 1
    while w <= workers:
        configfile_name = "/tmp/%s.%s" % (filename, w)
        create_config_file(parser, ports, configfile_name, used_ports)
        configfile_names.append(configfile_name)
        w += 1
    for (section, ports) in used_ports.items():
        worker_processes = subprocess.check_output(
            "grep processor /proc/cpuinfo | wc -l", shell=True)
        worker_processes = re.match("[0-9]+", worker_processes).group(0)
        context = {
            'worker_processes': worker_processes,
            'pid': '/tmp/nginx.%s.pid' % ports['main'],
            'server_name': get_fqdn(),
            'servers': [],
            'port': ports['main'],
            'doc_port': settings.doc_port,
            'root': settings.root,
            }
        for port in ports['processes']:
            context['servers'].append({
                    'host': 'localhost',
                    'port': port,
                })
        if 'ssl.privatekey' in values:
            context['privatekey'] = ("ssl_certificate_key %s;"
                % values['ssl.privatekey'])
        else:
            context['privatekey'] = None
        if 'ssl.certificate' in values:
            context['certificate'] = ("ssl_certificate %s;"
                % values['ssl.certificate'])
        else:
            context['certificate'] = None

        nginx_file = "/tmp/nginx.conf.%s" % ports['main']
        create_nginx_file(nginx_file, values['optional.nginx_tmpl'], context)
        nginx_files.append(nginx_file)

    return configfile_names, nginx_files

def create_config_file(parser, ports, configfile_name, used_ports):
    config = ConfigParser.RawConfigParser()
    for section in parser.sections():
        if section != 'optional':
            config.add_section(section)
            for (name, value) in parser.items(section):
                if (name == 'listen' and
                    section in ('jsonrpc', 'xmlrpc', 'webdab')):
                    host, port = value.split(':')
                    if section not in used_ports:
                        used_ports[section] = {
                            'main': port,
                            'processes': []
                            }
                    port2use = ports.pop()
                    used_ports[section]['processes'].append(port2use)
                    value = "%s:%s" % (host, port2use)
                config.set(section, name, value)
    with open(configfile_name, 'wb') as configfile:
        config.write(configfile)

def create_nginx_file(nginx_file, nginx_tmpl, context):
    if not jinja2_loaded:
        print "Could not found Jinja2 module"
        sys.exit(1)
    with open(nginx_tmpl, 'rb') as nf:
        t = nf.read()
    template = Jinja2Template(t)
    with open(nginx_file, 'wb') as configfile:
        configfile.write(template.render(context).encode('utf-8'))

def find_directory(root, directories):
    for directory in directories:
        path = os.path.join(root, directory)
        if os.path.isdir(path):
            return path
    return None

def start(settings):
    """
    Starts Tryton server.
    """

    server_directories = [
        'trytond',
        '.virtualenvs/monitoring',
        ]
    path = find_directory(settings.root, server_directories)
    if not path:
        print 'Could not find server directory.'
        sys.exit(1)

    # Set executable name
    call = ['python', '-u', os.path.join(path, 'bin', 'trytond')]

    if settings.logconf:
        call += ['--logconf', settings.logconf]

    if (not settings.config_multiserver or (settings.config_multiserver and
            settings.extra_arguments and ('-u' in settings.extra_arguments
            or '--all' in settings.extra_arguments))):
        if os.path.exists(settings.config):
            call += ['-c', settings.config]
        else:
            # If configuration file does not exist try to start the server anyway
            print 'Configuration file not found: %s' % settings.config

        if settings.database:
            call += ['--database', settings.database]
        if settings.dev:
            call += [settings.dev]
        if settings.cron:
            call += [settings.cron]
        if settings.verb:
            call += [settings.verb]

        call += settings.extra_arguments

        if settings.verbose:
            print "Calling '%s'" % ' '.join(call)

        # Create pidfile ourselves because if Tryton server crashes on start it may
        # not have created the file yet while keeping the process running.
        fork_and_call(call, pidfile=settings.pidfiles[0],
            logfile=settings.logfile)
    else:
        first = True
        for config in settings.config_multiserver:
            multicall = call[:]
            w = int(config.rpartition('.')[2]) - 1
            if os.path.exists(config):
                multicall += ['-c', config]
            else:
                print ('[MULTIPROCESS] Configuration file not found: %s'
                    % config)
                sys.exit(1)

            if settings.database:
                multicall += ['--database', settings.database]
            if first:
                first = False
                if settings.cron:
                    multicall += [settings.cron]

            if settings.verbose:
                print "Calling '%s'" % ' '.join(multicall)

            fork_and_call(multicall, pidfile=settings.pidfiles[w],
                logfile=settings.logfile)
        start_nginx(settings.config_nginx)

def start_nginx(config_nginx):
    for nginx in config_nginx:
        nginxcall = ('/usr/sbin/nginx', '-c', nginx)
        subprocess.Popen(nginxcall, stdout=None, stderr=None)

def stop(pidfiles, warning=True):
    """
    Stops Tryton's application server/s and JasperServer.

    If warning=True it will show a message to the user when pid file does
    not exist.
    """
    for pidfile in pidfiles:
        if not pidfile:
            continue
        if not os.path.exists(pidfile):
            if warning:
                print 'Pid file %s does not exist.' % pidfile
            continue
        pid = open(pidfile, 'r').read()
        try:
            pid = int(pid)
        except ValueError:
            continue
        try:
            os.kill(pid, 9)
        except OSError:
            print ("Could not kill process with pid %d. Probably it's no "
                "longer running." % pid)
        finally:
            try:
                os.remove(pidfile)
            except OSError:
                print "Error trying to remove pidfile %s" % pidfile

def stop_nginx(config_nginx):
    for nginx in config_nginx:
        call = ('/usr/sbin/nginx', '-c', nginx, '-s', 'stop')
        subprocess.Popen(call, stdout=None, stderr=None)

def tail(filename, settings):
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
        if (settings.extra_arguments and ('-u' in settings.extra_arguments
                   or '--all' in settings.extra_arguments)
                and 'Update/Init succeed!' in line):
                return False

    except KeyboardInterrupt:
        print "Server monitoring interrupted. Server will continue working..."
    finally:
        file.close()
    return True

def top(pidfile):
    pid = open(pidfile, 'r').read()
    try:
        pid = int(pid)
    except ValueError:
        print "Invalid pid number: %s" % pid
        return
    while True:
        os.kill(pid, signal.SIGUSR1)
        time.sleep(1)

def backtrace(pidfile):
    pid = open(pidfile, 'r').read()
    try:
        pid = int(pid)
    except ValueError:
        print "Invalid pid number: %s" % pid
        return
    while True:
        os.kill(pid, signal.SIGUSR2)
        time.sleep(1)

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

if settings.action == 'config':
    try:
        print open(settings.config, 'r').read()
        sys.exit(0)
    except IOError:
        sys.exit(255)

if settings.action == 'ps':
    ps()

if settings.action == 'db':
    db()

config = load_config(settings.config, settings)

if settings.action == 'top':
    for pidfile in settings.pidfiles:
        top(pidfile)

if settings.action == 'console':
    console(settings)
    sys.exit(0)

if settings.action == 'backtrace':
    for pidfile in settings.pidfiles:
        backtrace(pidfile)

if settings.action in ('start', 'restart', 'krestart'):
    if os.path.exists('doc/user'):
        fork_and_call(['make', 'html'], cwd='doc/user', logfile='doc.log')
    else:
        print "No user documentation available."

if settings.action in ('stop', 'restart', 'krestart'):
    stop(settings.pidfiles)
    stop([settings.pidfile_jasper], warning=False)
    kill_process('celery', 'celery')
    if settings.config_nginx:
        stop_nginx(settings.config_nginx)

if settings.action in ('kill', 'krestart'):
    kill()

if settings.action in ('start', 'restart', 'krestart'):
    backup_and_remove(settings.logfile)
    start(settings)

    if settings.tail:
        # Ensure server.log has been created before executing 'tail'
        time.sleep(1)
        tail_out = tail(settings.logfile, settings)

        if not tail_out:
            settings = parse_arguments(sys.argv, root, False)
            settings.root = root
            config = load_config(settings.config, settings)
            start(settings)
            tail(settings.logfile, settings)

if settings.action == 'status':
    tail(settings.logfile, settings)
