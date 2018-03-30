#!/bin/bash

# generate email containing current PetaLibrary Active usage info

# Peter Ruprecht - 1/27/2014

export PATH=/usr/lpp/mmfs/bin:${PATH}

ldapserver=directory01
filesystem=gpfs01
filesystemdir=/gpfs/${filesystem}
emailrcpts=thomas.hauser@colorado.edu
diskusagefile=${filesystemdir}/mmFilesetQuotaStatus.log
#tapequotafile=${filesystemdir}/tape.quota

# Mailing info
REPLYTO="rc-help@colorado.edu"
#BCC="peter.ruprecht@colorado.edu"
BCC=daniel.milroy@colorado.edu,pabi5658@colorado.edu,jonathon.anderson@colorado.edu
DATE=`date +"%B %Y"`

  # get raw data for email report
  rawdata=`mmrepquota --block-size auto -j gpfs01 | grep -v rc_scratch | grep -v mcdbtest`
  # get total TB available in filesystem
  filesystem_avail=`df -B 1T /dev/gpfs01 | tail -1 | awk '{print $4}'` # in TB
  # sum quotas
  totaldiskquota=`mmrepquota --block-size T -j $filesystem | grep FILESET | grep -v mcdbtest \
    | grep -v rc_scratch | grep -v csdms | grep -v Echo360 | awk '{sum+=$5} END {print sum}' ` # in TB
  # sum inodes
  totalinodes=`mmrepquota --block-size T -j $filesystem | grep FILESET | grep -v mcdbtest \
    | grep -v rc_scratch | awk '{sum+=$9} END {print sum}' ` 
  # get current usage 
  totaldiskusage_gb=`mmrepquota --block-size G -j $filesystem | grep FILESET | grep -v mcdbtest \
    | grep -v rc_scratch | grep -v csdms | grep -v Echo360 | awk '{sum+=$3} END {print sum}' `  # in GB
  totaldiskusage=`echo "scale=3; ${totaldiskusage_gb}/1000" | bc`  # in TB
  
  mail -s "PetaLibrary Active capacity report - ${DATE}" -r ${REPLYTO} -b $BCC $emailrcpts << EOF

-- ${DATE} usage report for CU PetaLibrary Active Storage --

Current disk space usage by customers is ${totaldiskusage} TB, out of ${totaldiskquota} TB purchased.

The GPFS filesystem currently has ${filesystem_avail} TB available.  

The total number of files and directories used is ${totalinodes}.

Here is the raw data:

$rawdata

Thanks,
Research Computing
EOF

