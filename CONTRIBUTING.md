# Contributing to mssql-backup

## Preface

As mssql-backup is bearing the GPLv2 license, anyone is free to take the code and adapt it to their needs within the boundaries of said license.

At the time of writing MS SQL Server running on Linux cannot make use of Maintenance Plans, so a backup script is needed to create backups. When I searched for existing backup scripts that would do the job, I found quite a number of them, but none of them seemed to do entirely what I felt was needed to create backups with as less effort as possible. Therefore, I searched for some reference material and created this script.

I've put quite some hours into this script, and even though I do not claim it will be flawless I decided to share it with the world. You are free to use it when it suits your needs. If there is something wrong or missing and you're able to enhance the script; please fork the project and submit a Pull Request to share the corrections or enhancements with me.

That said, even though the [Microsoft documentation for installing SQL Server](https://docs.microsoft.com/en-us/sql/linux/quickstart-install-connect-red-hat?view=sql-server-ver15#install) on Linux instructs to install Python 2, I do not see the need to make the script Python 2 compatible. When running MS SQL Server, the supported OS-es are recent enough OS to support Python 3.

## Code style

I may have a particular code style to you. I think that everyone has their own style, and that's fine: I'll keep mine unless I come to the conclusion that there are good reasons not to.

When contributing code to this project I ask that you adhere to the code style of this script. Much of it can be derived from just reading it since it's not that complicated. However, below are a few guidelines to avoid unnecessary confusion or discussion.

- UPPERCASE is used for top-level variables. LOWERCASE is used for local variables, prefixed with an underscore. This is to avoid confusion about which type of variable (top-level or local) you're dealing with when reading the code, and to make local variables stand out from Python functions.
- When quoting strings, single-quotes are used wherever possible. When concat-ing strings, the `format()` function is used to do this because I find it more readable than plus-ing the string together.
- When writing a new function, please add function documentation of its purpose; even when it should be clear by reading the function name. Yes, I'm using three double-quotes for this.
- When using functions that may fail and throw exceptions, please use a `try-except(-else)` block to fetch any exception that can occur so the script can either continue or terminate gracefully with some meaningful and readable error message in the log file.
- Yes: `if (DEBUG is true):` is the same as `if (DEBUG):` or `if DEBUG:`.
  - Round brackets are used to construct any condition block. It is indeed not necessary in most cases, but when more complex conditions are required, parenthesis are likely needed anyway to group the conditions properly. Using them always makes the code look more consistent.
  - Even though code like `if DEBUG:` has the equal effect of code like `if (DEBUG is True):`, the latter is more precise.
- When appropriate, please setup some basic `log_line()` lines so that when something fails, there is more debugging information available in the log file.
