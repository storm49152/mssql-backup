# mssql-backup

## About

This Python script creates backups from MS SQL Server databases which are `ONLINE`. It is specifically meant to be run on Linux.

It will do both data and transaction log backups.

The script does not output anything to the console; instead it will create a new log file each time it is run.

## Configuration

Please check the configuration variables in the top of the script and change to your needs. The configuration decides:

- Where the log file is created.
- How `pyodbc` is configured to connect to MS SQL Server.
- Which databases are excluded from backup by default.
- The backup type schedule.
- Which backup options are used for each backup type.

> MS SQL Server should be configured with a `defaultbackupdir` directory in `/var/opt/mssql/mssql.conf`. This is where backup files will be created.

## Usage

```shell
mssql-backup.py [-m] [-t] [-i] [-l] [-d]
```

`'-m', '--mode'`

- Override the backup mode.
- Valid backup modes are: `data`, `tr` (where `tr` means: transaction log).
- Default backup mode: `data`.

According to MS documentation: "During a full or differential database backup, SQL Server backs up enough of the transaction log to produce a consistent
database when the backup is restored." Therefore, it is not necessary to do both a Full or Differential backup together with a Transaction Log backup, and hence there is no backup mode that does both at the same time.

> If you want to create multiple transaction log backups per day, just create a `cron` job which overrides the backup mode to `tr`.

> When selecting `tr` mode, the script will only try to create a transaction log backup from databases which have the Recovery Model configured to either `full` or `bulk`.

`'-t', '--type'`

- Override the backup type.
- Valid backup types: `full`, `differential`, `schedule`.
- Default backup type: `schedule`.

The script is created with the idea that you normally take only one backup per day. To facilitate this, there exists a backup type table that specifies which type of backup should be made depending on at which day you start the script. If you don't specify `-t` or set it explicitly to `schedule`, then the schedule decides which backup type is picked. If this doesn't suit your needs you can either:

- Modify the backup type table to your needs.
- Specify the backup type when the script starts, which will override the schedule.

`'-i', '--include'`

This parameter overrides the databases to backup. It accepts a comma-separated list of database names.

By default, the script creates a data backup from all databases, except from: 'master', 'model', 'msdb' and 'tempdb' (this is configurable in the script, adapt to your needs). This parameter lets you override this behavior. When this parameter is specified, it will override the exclude list in the script.

`'-l', '--list'`

Show a list of known database names which are ONLINE in JSON format.

`'-d', '--debug'`

Prints messages to the console while the script is running.

## Examples

Run with all defaults:

```shell
mssql-backup.py
```

Run a transaction log backup:

```shell
mssql-backup.py --mode tr
```

Run a data backup from one specific database:

```shell
mssql-backup.py --include my_special_db
```

Run a full data backup from one specific database, overriding the backup type schedule:

```shell
mssql-backup.py --type full --include my_special_db
```

## Todo

Work is being done for uploading backup files into a GCP bucket.

## Sources

- [Backup and restore SQL Server databases on Linux](https://docs.microsoft.com/en-us/sql/linux/sql-server-linux-backup-and-restore-database?view=sql-server-ver15)
- [BACKUP [Transact-SQL]](https://docs.microsoft.com/en-us/sql/t-sql/statements/backup-transact-sql?view=sql-server-ver15#arguments)
- [Python SQL Driver - pyodbc](https://docs.microsoft.com/en-us/sql/connect/python/pyodbc/python-sql-driver-pyodbc?view=sql-server-ver15)
- [pyodbc documentation](https://github.com/mkleehammer/pyodbc/wiki)
