#!/bin/bash

# report disk/tape usage in PL Archive

export PATH=/usr/lpp/mmfs/bin:${PATH}

# Mailing info
REPLYTO="rc-help@colorado.edu"
#BCC="peter.ruprecht@colorado.edu"
BCC=daniel.milroy@colorado.edu,jonathon.anderson@colorado.edu,pabi5658@colorado.edu
DATE=`date +"%B %Y"`
emailrcpts=thomas.hauser@colorado.edu

filesystem=archive01
filesystemdir=/gpfs/${filesystem}
emailfile=${filesystemdir}/user.email
diskusagefile=${filesystemdir}/mmFilesetQuotaStatus.log
tapequotafile=${filesystemdir}/tape.quota
tmpfile=/tmp/SGe3907sljg9x9l


echo "" > $tmpfile
echo "-- ${DATE} usage report for CU PetaLibrary Archive Storage -- " >> $tmpfile
echo "" >> $tmpfile

# per-project info

echo "Per-Project Info:" >> $tmpfile
echo "Capacity units are TB" >> $tmpfile
printf "%-28s%11s%11s%10s%10s%11s%11s%10s\n" Project TotalUsage TotalQuota DiskUsage DiskQuota InodeUsage InodeQuota TapeUsage >> $tmpfile
for project in `cat $emailfile | grep @ | grep -v ^# | awk '{print $1}'`; do 
  totalquota=`grep "^${project} " $tapequotafile | awk '{print $2}'` 
  inodequota=`mmrepquota --block-size G -j $filesystem | grep "^${project} " | awk '{print $12}'`  
  diskquota_gb=`mmrepquota --block-size G -j $filesystem | grep "^${project} " | awk '{print $6}'`  
  diskquota=`echo "scale=3; ${diskquota_gb}/1000" | bc`
  if [ -f $filesystemdir/$project/occupancy.log ]; then 
    totalusage_mb=`tail -1 $filesystemdir/$project/occupancy.log | awk '{ print $(NF-1) }' | cut -d: -f2` 
    totalusage=`echo "scale=3; ${totalusage_mb}/1000/1000" | bc` 
    diskusage_mb=`tail -1 $filesystemdir/$project/occupancy.log | awk '{ print $(NF) }' | cut -d: -f2` 
    diskusage=`echo "scale=3; ${diskusage_mb}/1000/1000" | bc` 
  else     
    totalusage="0"     
    diskusage="0" 
  fi 
  inodeusage=`mmrepquota --block-size G -j $filesystem | grep "^${project} " | awk '{print $10}'` 
  tapeusage=`echo "scale=3; ${totalusage} - ${diskusage}" | bc` 
  printf "%-28s%11s%11s%10s%10s%11s%11s%10s\n" $project $totalusage $totalquota $diskusage $diskquota $inodeusage $inodequota $tapeusage >> $tmpfile
  #echo $project $totalusage $totalquota 
done

# Tape system info

echo "" >> $tmpfile
echo "Tape system usage report:" >> $tmpfile
#dsmadmc -id=admin -pa=sQue3+xcn Q auditoccupancy | tail -13 | head -11 >> $tmpfile
dsmadmc -id=admin -pa=sQue3+xcn  -displaymode=list Q auditoccupancy | tail -22 |head -19 >> $tmpfile

# General filesystem info

  # get raw data for email report
  rawdata=`mmrepquota --block-size auto -j $filesystem `
  # get total TB available in filesystem
  filesystem_avail=`df -B 1T /dev/$filesystem | tail -1 | awk '{print $4}'` # in TB
  # get current usage 
  totaldiskusage_gb=`mmrepquota --block-size G -j $filesystem | grep FILESET | \
    grep -v "^root " | awk '{sum+=$4} END {print sum}' `  # in GB
  totaldiskusage=`echo "scale=3; ${totaldiskusage_gb}/1000" | bc`  # in TB
  
echo "" >> $tmpfile
echo "" >> $tmpfile
echo "GPFS Filesystem Info:" >> $tmpfile

echo "Current disk space usage by customers is ${totaldiskusage} TB." >> $tmpfile
echo "" >> $tmpfile
echo "The GPFS filesystem currently has ${filesystem_avail} TB available.  " >> $tmpfile
echo "" >> $tmpfile
echo "Here is the GPFS raw data:" >> $tmpfile
echo "" >> $tmpfile
echo "$rawdata" >> $tmpfile

# mail the report
mail -s "PetaLibrary Archive capacity report - ${DATE}" -r ${REPLYTO} -b $BCC $emailrcpts < $tmpfile

# clean up
rm $tmpfile
