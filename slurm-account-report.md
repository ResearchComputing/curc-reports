# slurm-account-report.py

`slurm-account-report.py` is a wrapper and automation script for
standard Slurm accounting commands `sacct`, `sacctmgr`, and
`sshare`. It is used to generate and distribute monthly Slurm account
reports in the RC environment, but may also be run at any time by
regular users, support staff, and operators.

`slurm-account-report.py` has relatively complete on-line `--help`.

```
usage: slurm-account-report.py [-h] [-s TIME_STRING] [-e TIME_STRING]
                               [-M CLUSTERS] [--email ADDRESS] [--batch CSV]
                               [--no-fairshare] [--quiet] [--verbose]
                               [--debug] [--noop]
                               [accounts [accounts ...]]

Generate activity reports for Slurm accounts.

positional arguments:
  accounts              List of slurm accounts to include in report

optional arguments:
  -h, --help            show this help message and exit
  -s TIME_STRING, --starttime TIME_STRING
                        Reporting period start time as Slurm TIME_STRING.
                        Default: the start of the previous month.
  -e TIME_STRING, --endtime TIME_STRING
                        Reporting period end time as Slurm TIME_STRING.
                        Default: the start of the current month.
  -M CLUSTERS, --clusters CLUSTERS
                        Comma-separated list of clusters to include in report
  --email ADDRESS       Send report to ADDRESS
  --batch CSV           Read accounts, clusters, and email addresses from CSV
  --no-fairshare        Do not include fairshare information in report
  --quiet               Suppress logging of non-critical events to console
  --verbose             Log informational events to console
  --debug               Log debug events to console
  --noop                Do not send reports via email, even when email
                        addresses are provided
```


## Examples

### Report for a single account

```
python slurm-account-report.py --clusters=blanca blanca-curc
```

### Report for multiple accounts

```
python slurm-account-report.py --clusters=blanca blanca-curc blanca-curc-gpu
```

### Report for a different time period

```
python slurm-account-report.py --clusters=blanca --starttime=2018-01-01 --endtime=2018-02-01 blanca-curc-gpu
```

Note that fairshare data always reflects the time the report was
generated, and is not affected by the specified reporting period. You
may want to omit fairshare data from such reports.

```
python slurm-account-report.py --clusters=blanca --starttime=2018-01-01 --endtime=2018-02-01 --no-fairshare curc-gpu
```
