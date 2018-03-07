#!/bin/bash

# generate email to PI and PoC for each project containing
# current usage info (disk and file number), quotas, and
# users.

# Peter Ruprecht - 9/17/2013
#  updated 2/28/2014 to account for mix of data on tape and disk

export PATH=/usr/lpp/mmfs/bin:${PATH}

ldapserver=directory01
filesystem=archive01
filesystemdir=/gpfs/${filesystem}
emailfile=${filesystemdir}/user.email
diskusagefile=${filesystemdir}/mmFilesetQuotaStatus.log
tapequotafile=${filesystemdir}/tape.quota

# Mailing info
REPLYTO="rc-help@colorado.edu"
BCC=daniel.milroy@colorado.edu,pabi5658@colorado.edu,jonathon.anderson@colorado.edu
#SUBJECT="RC Petalibrary Quota"
DATE=`date +"%B %Y"`

for project in `cat $emailfile | grep @ | grep -v ^# | awk '{print $1}'`; do
  # get quotas
  diskquota=`grep "^${project} " $tapequotafile | awk '{print $2}'` # in TB
  inodequota=`mmrepquota --block-size G -j $filesystem | grep "^${project} " | awk '{print $12}'`
  # get current usage 
  if [ -f $filesystemdir/$project/occupancy.log ]; then
    totalusage_mb=`tail -1 $filesystemdir/$project/occupancy.log | awk ' { print $(NF-1) }' | cut -d: -f2`  #in MB
    totalusage=`echo "scale=3; ${totalusage_mb}/1000/1000" | bc`  # in TB
    diskusage_mb=`tail -1 $filesystemdir/$project/occupancy.log | awk ' { print $(NF) }' | cut -d: -f2`  #in MB
    diskusage=`echo "scale=3; ${diskusage_mb}/1000/1000" | bc`  # in TB
  else
    totalusage="0"
    diskusage="0"
  fi
  inodeusage=`mmrepquota --block-size G -j $filesystem | grep "^${project} " | awk '{print $10}'`
  tapeusage=`echo "scale=3; ${totalusage} - ${diskusage}" | bc` # in TB
  # Get email addrs
  recipients=`grep "^${project} " $emailfile | awk '{print $2}'`
  #echo "$project is using $diskusage TB of $diskquota TB quota and $inodeusage files of $inodequota allowed"
  # find owning group and member users
  grp=`ls -ld ${filesystemdir}/${project} | awk '{print $4}'`
  userids=`ldapsearch -x -LLL -H ldap://${ldapserver} -b ou=Groups,dc=rc,dc=colorado,dc=edu gidNumber=$grp | grep ^memberUid | awk '{print $2}'`
  users=""
  for usr in $userids; do
    fullname=`ldapsearch -x -LLL -H ldap://${ldapserver} -b ou=People,dc=rc,dc=colorado,dc=edu uid=$usr | grep ^cn: | cut -d\  -f2-`
    #echo "$usr  -  $fullname"
    users="${users}
${usr}  -  ${fullname}"
  done
  #mail -s "PetaLibrary Report - ${DATE}" -r ${REPLYTO} peter.ruprecht@colorado.edu << EOF
  mail -s "PetaLibrary Report - ${DATE}" -r ${REPLYTO} -b $BCC $recipients << EOF
${DATE} usage report for your Archive project named "${project}"

Current usage is ${totalusage} TB out of your ${diskquota} TB storage quota, and ${inodeusage} files of ${inodequota} allowed.

Users currently allowed filesystem access to the project are: ${users}

Reminder: Please acknowledge the PetaLibrary in any publications that were aided by its use.  A sample acknowledgement is at https://www.rc.colorado.edu/services/storage/petalibrary.  Also, remember that HIPAA, FERPA, ITAR, classified, or Personally-Identifiable data may not be stored on the PetaLibrary.

Please reply to this email if you have any questions.

Thanks,
Research Computing
EOF

done
