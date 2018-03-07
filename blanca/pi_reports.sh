#!/bin/bash

MONTH=`date +%B --date="1 month ago"`
read Y M <<< `date +"%Y %m" --date="1 month ago"`
# Last day of previous month
L=`date -d "-$(date +%d) day" +%d`

for i in `cat /curc/slurm/blanca/pi-email.txt`
do
  QOS=`echo $i | awk -F ':' '{print $1}'`
  EMAIL=`echo $i | awk -F ':' '{print $2}'`
  COMMAND="/curc/slurm/blanca/scripts/ssumm -s ${Y}-${M}-01 -e ${Y}-${M}-${L} -q ${QOS} | mail -s \"Blanca Usage Report ${MONTH} ${Y}\" -S from=slurm@rc.colorado.edu -S replyto=rc-help@colorado.edu -b jonathon.anderson@colorado.edu ${EMAIL}"
  eval $COMMAND
done

