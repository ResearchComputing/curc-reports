Automated and random-access reports for RC services


## Legacy scripts and deployments

* `/curc/slurm/blanca/scripts/pi_reports.sh` (in `slurm3` crontab)
* `/gpfs/archive01/custreport.sh` (in `petatsm01` crontab)
* `/gpfs/archive01/capacityreport.sh` (in `petatsm01` crontab)


## Blanca

* `pi_reports.sh`, monthly usage email script
* `ssumm`, called from `pi_reports.sh`
* `pi-email.txt`, input data mapping target emails for Blanca accounts


## Summit

* `pi-report-summit.sh`, presumably a port of the Blanca
  `pi_reports.sh`
* `ssumm-summit`, called from `pi-report-summit.sh`
* `pi-email-summit.txt`, input data mapping target emails for Summit
  accounts


## PetaLibrary

* `capacityreport.sh`
* `custreport.sh`
* `tape.quota`
* `user.email`
