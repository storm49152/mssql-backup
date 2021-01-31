#!/bin/env python3

"""
Date:    2021-01-29
Author:  storm49152
License: GPLv2
"""


import argparse
import socket
import pathlib
import pyodbc
import json
from os import path
from datetime import datetime


MY_HOSTNAME     = socket.getfqdn()
NOW             = datetime.now().strftime('%Y%m%d-%H%M%S')
WEEKDAY         = datetime.now().strftime('%w')

LOG_DIR         = '/var/log/mssql'

DB_DRIVER       = '{ODBC Driver 17 for SQL Server}'
DB_HOST         = '127.0.0.1'
DB_PORT         = 1433
DB_USER         = 'the backup user'
DB_PASS         = 'the super secret password'
# DB_INCLUDES overrides DC_EXCLUDES, see commandline arguments.
DB_EXCLUDES     = [ 'master', 'model', 'msdb', 'tempdb',]

# The backup type schedule is zero-based.  Day 0 is Sunday, day 6 is Saturday.
BKP_TYPE_SCHEDULE = {
    '0': 'full',
    '1': 'differential',
    '2': 'differential',
    '3': 'differential',
    '4': 'differential',
    '5': 'differential',
    '6': 'differential',
}
BKP_OPTIONS     = {
    'full': [
        'NOFORMAT',
        'NOINIT',
        'NAME = N\'{0}-full\'',
        'SKIP',
        'NOREWIND',
        'NOUNLOAD',
        'STATS = 10',
    ],
    'differential': [
        'DIFFERENTIAL',
        'NOFORMAT',
        'NOINIT',
        'NAME = N\'{0}-differential\'',
        'SKIP',
        'NOREWIND',
        'NOUNLOAD',
        'STATS = 10',
    ],
    'transaction_log': [
        'NOFORMAT',
        'NOINIT',
        'NAME = N\'{0}-TR\'',
        'SKIP',
        'REWIND',
        'NOUNLOAD',
        'STATS = 10',
    ],
}


def get_args():
    """
    Fetch commandline parameters.
    """
    _description = 'Backup MSSQL databases. By default all known ONLINE databases will be backed up, except for: "{0}".'.format(
        '", "'.join(DB_EXCLUDES))
    _p = argparse.ArgumentParser(description=_description)
    _p.add_argument('-m', '--mode', dest='bkp_mode', action='store', type=str, default='data',
                    help='Override the backup mode. Valid: "data", "tr" (lowercase). Default: "data".')
    _p.add_argument('-t', '--type', dest='bkp_type', action='store', type=str, default='schedule',
                    help='Override the backup type. Valid: "full", "differential", "schedule" (lowercase). Default: "schedule.')
    _p.add_argument('-i', '--include', dest='db_includes', action='store', type=str, default=None,
                    help='Override the databases to backup. Accepts a comma-separated list of database namess.')
    _p.add_argument('-l', '--list', dest='db_list', action='store_true', default=False,
                    help='Show a list of known database names which are ONLINE in JSON format.')
    _p.add_argument('-d', '--debug', dest='debug', action='store_true', default=False,
                    help='Print debug messages to the console.')
    _a = _p.parse_args()

    _bkp_mode = _a.bkp_mode.lower()
    _bkp_type = _a.bkp_type.lower()

    if (_bkp_mode not in ['data', 'tr']):
        print('ERROR: invalid mode: {0}'.format(_bkp_mode))
        print('Valid modes: "data", "tr" (lowercase).')
        exit(1)

    if (_bkp_type not in ['full', 'differential', 'schedule']):
        print('ERROR: invalid backup type: {0}'.format(_bkp_type))
        print('Valid backup types: "full", "differential", "schedule" (lowercase).')
        exit(1)

    return _a.debug, _bkp_mode, _bkp_type, _a.db_includes, _a.db_list


def log_line(_msg):
    """
    Send a line to the logfile.
    """
    global DEBUG, LOG_DIR, NOW

    if (not path.isdir(LOG_DIR)):
        pathlib.Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

    _log_file = '{0}/backup-{1}.log'.format(LOG_DIR, NOW)
    _now      = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if (DEBUG == True): print(_msg)

    with open(_log_file, 'a+') as _f:
        _f.write("{0} {1}\n".format(_now, _msg))


def mssql_connect():
    """
    Connect to the database and return a handle on success.
    """
    global DEBUG, DB_DRIVER, DB_HOST, DB_PORT, DB_USER, DB_PASS

    if DEBUG: print('[mssql_connect()]')

    try:
        if DEBUG: print('[mssql_connect()] Connecting to database')
        log_line('[mssql_connect] Connect to database server: {0}:{1}'.format(DB_HOST, DB_PORT))

        _cn = pyodbc.connect('Driver={0}; Server={1}; Port={2}; UID={3}; PWD={4}'.format(
            DB_DRIVER, DB_HOST, DB_PORT, DB_USER, DB_PASS))
    except pyodbc.Error as _e:
        _line = 'ERROR: [{0}] {1}'.format(_e.args[0], _e.args[1])
        print(_line)
        log_line(_line)
        exit(_e.args[0])
    else:
        if DEBUG: print('[mssql_connect()] Connected to database')

        # To prevent error:
        # pyodbc.ProgrammingError: ('42000', '[42000] [Microsoft][ODBC Driver 17 for SQL Server][SQL Server]
        # Cannot perform a backup or restore operation within a transaction. (3021) (SQLExecDirectW)')
        _cn.autocommit = True

        return _cn


def mssql_query(_cn, _sql, _fetchall=False, _nextset=False):
    """
    Execute the SQL query, handle exceptions and return the result.
    """
    global DEBUG

    _cur = _cn.cursor()
    _query = None

    try:
        if (_fetchall == True):
            _query = _cur.execute(_sql).fetchall()
        else:
            _query = _cur.execute(_sql)
        if (_nextset == True):
            while _cur.nextset(): pass
    except pyodbc.NotSupportedError as _e:
        log_line('ERROR: Operation Not Supported [{0}]'.format(_e.args[0]))
        log_line('ERROR: {1}'.format(_e.args[1]))
    except pyodbc.IntegrityError as _e:
        log_line('ERROR: Integrity Error [{0}]'.format(_e.args[0]))
        log_line('ERROR: {1}'.format(_e.args[1]))
    except pyodbc.DataError as _e:
        log_line('ERROR: Data Error [{0}]'.format(_e.args[0]))
        log_line('ERROR: {1}'.format(_e.args[1]))
    except pyodbc.ProgrammingError as _e:
        log_line('ERROR: Programming Error [{0}]'.format(_e.args[0]))
        log_line('ERROR: {1}'.format(_e.args[1]))
    except pyodbc.OperationalError as _e:
        log_line('ERROR: Operational Error [{0}]'.format(_e.args[0]))
        log_line('ERROR: {1}'.format(_e.args[1]))

    _cur.close()

    return _query


def mssql_get_dbs(_cn):
    """
    Fetch a list of ONLINE MSSQL databases and their recovery model.
    """
    global DEBUG, DB_EXCLUDES, DB_INCLUDES

    if DEBUG: log_line('[mssql_get_dbs()]')

    _sql = 'SELECT name, recovery_model_desc FROM sys.Databases WHERE state_desc = \'ONLINE\''
    _query = mssql_query(_cn, _sql, True, False)

    _dbs = []
    if (DB_INCLUDES is None):
        [_dbs.append({'name': _db[0], 'recovery_model': _db[1]}) for _db in _query if _db[0] not in DB_EXCLUDES]
    else:
        [_dbs.append({'name': _db[0], 'recovery_model': _db[1]}) for _db in _query if _db[0] in DB_INCLUDES]

    return _dbs


def mssql_show_dbs(_dbs):
    """
    Show a list of databases in JSON format.
    """
    print(json.dumps(_dbs))


def mssql_backup_data(_cn, _dbs):
    """
    Create data backups from the specified databases.
    """
    global BKP_TYPE

    _bkp_files = []

    for _db in _dbs:
        _now = datetime.now().strftime('%Y%m%d-%H%M%S')

        # Fetch the backup type based on the schedule or commandline argument.
        if (BKP_TYPE == 'schedule'):
            _bkp_type = BKP_TYPE_SCHEDULE[WEEKDAY]
        else:
            _bkp_type = BKP_TYPE

        # Set the backup filename based on the backup type.
        _file = None
        if (_bkp_type == 'full'):
            _file = '{0}-FULL-{1}.bak'.format(_db['name'], _now)
        if (_bkp_type == 'differential'):
            _file = '{0}-DIFF-{1}.bak'.format(_db['name'], _now)
        _bkp_files.append(_file)

        # Create the SQL statement to backup the database.
        _bkp_options = ', '.join(BKP_OPTIONS[_bkp_type]).format(_db['name'])
        _sql = 'BACKUP DATABASE [{0}] TO DISK = N\'{1}\' WITH {2}'.format(_db['name'], _file, _bkp_options)
        if (DEBUG == True): log_line('[mssql_backup_tr][_sql] {0}'.format(_sql))

        log_line('[mssql_backup_data] Backup database Data ({0}): {1}'.format(_bkp_type, _db['name']))
        log_line('[mssql_backup_data] Backup file: {0}'.format(_file))

        # Perform the backup.
        mssql_query(_cn, _sql, False, True)

        log_line('[mssql_backup_data] Done')

    return _bkp_files


def mssql_backup_tr(_cn, _dbs):
    """
    Create Transaction Log backups from the specified databases which have the
    "FULL" recovery_model configured.
    """
    global DEBUG

    _bkp_files = []

    for _db in _dbs:
        _now = datetime.now().strftime('%Y%m%d-%H%M%S')

        if (_db['recovery_model'] == 'FULL' or _db['recovery_model'] == 'BULK'):
            # Set the backup filename,
            _file = '{0}-{1}.trn'.format(_db['name'], _now)
            _bkp_files.append(_file)

            # Create the SQL statement to backup the Transaction Log.
            _bkp_options = ', '.join(BKP_OPTIONS['transaction_log']).format(_db['name'])
            _sql = 'BACKUP LOG [{0}] TO DISK = N\'{1}\' WITH {2}'.format(_db['name'], _file, _bkp_options)
            if (DEBUG == True): log_line('[mssql_backup_tr][_sql] {0}'.format(_sql))

            log_line('[mssql_backup_tr] Backup database Transaction Log: {0}'.format(_db['name']))
            log_line('[mssql_backup_tr] Backup file: {0}'.format(_file))

            # Perform the backup.
            mssql_query(_cn, _sql, False, True)

            log_line('[mssql_backup_tr] Done')
        else:
            log_line('[mssql_backup_tr] Not backing up the Transaction log: Recovery mode is not FULL or BULK: {0} ({1})'.format(
                _db['name'], _db['recovery_model']))

    return _bkp_files


def main():
    """
    Main function.
    """
    global BKP_MODE, DB_LIST

    _cn = mssql_connect()
    _dbs = mssql_get_dbs(_cn)
    if (DB_LIST == True):
        mssql_show_dbs(_dbs)
    else:
        if (BKP_MODE == 'data'):
            _bkp_files = mssql_backup_data(_cn, _dbs)
        if (BKP_MODE == 'tr'):
            _bkp_files = mssql_backup_tr(_cn, _dbs)


if __name__ == '__main__':
    # Fetch commandline arguments into global variables.
    DEBUG, BKP_MODE, BKP_TYPE, DB_INCLUDES, DB_LIST = get_args()

    log_line('=== Backup begin ===')

    main()

    log_line('=== Backup end ===')
