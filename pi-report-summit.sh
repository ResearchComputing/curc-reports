#!/bin/bash

MONTH=`date +%B --date="1 month ago"`
read Y M <<< `date +"%Y %m" --date="1 month ago"`
# Last day of previous month
L=`date -d "-$(date +%d) day" +%d`

for i in `cat /projects/ruprech/slurm-scripts/pi-email-summit.txt | grep -v '^#'`
do
  ALLOC=`echo $i | awk -F ':' '{print $1}'`
  EMAIL=`echo $i | awk -F ':' '{print $2}'`
  COMMAND="/projects/ruprech/slurm-scripts/ssumm-summit -s ${Y}-${M}-01T00:00:00 -e ${Y}-${M}-${L}T23:59:59 -A ${ALLOC} | mail -s \"Summit Usage Report ${MONTH} ${Y} - ${ALLOC} \" -S from=slurm@rc.colorado.edu -S replyto=rc-help@colorado.edu -b rc-ops@colorado.edu ${EMAIL}"
  eval $COMMAND
done

