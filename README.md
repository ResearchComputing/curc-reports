Automated and random-access reports for RC services




## Slurm

* `slurm-account-report.py`, Generate reports for Slurm accounts


## Monthly reports

* `blanca-monthly-reports.csv`, a map of recipients and accounts for monthly reporting
* `summit-monthly-reports.csv`, a map of recipients and accounts for monthly reporting

RMACC Summit and Blanca Slurm account reports are automated by `cron`
running on `slurmdb1`.

```
0 6 1 * * slurm /usr/bin/python /curc/admin/rc-reports/slurm-account-report.py --batch /curc/admin/rc-reports/blanca-monthly-reports.csv --no-fairshare --quiet
0 7 1 * * slurm /usr/bin/python /curc/admin/rc-reports/slurm-account-report.py --batch /curc/admin/rc-reports/summit-monthly-reports.csv --quiet
```


## PetaLibrary

* `capacityreport-active.sh`
* `custreport-active.sh`
* `capacityreport-archive.sh`
* `custreport-archive.sh`
* `tape.quota`
* `user.email`


### Legacy scripts and deployments

* `/gpfs/archive01/custreport.sh` (in `petatsm01` crontab)
* `/gpfs/archive01/capacityreport.sh` (in `petatsm01` crontab)
* `/gpfs/gpfs01/custreport.sh` (in `gs01` crontab)
* `/gpfs/gpfs01/capacityreport.sh` (in `gs01` crontab)
