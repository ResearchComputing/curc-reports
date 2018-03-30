#!/bin/bash

# generate email to PI and PoC for each project containing
# current usage info (disk and file number), quotas, and
# users.

# Peter Ruprecht - 9/17/2013

export PATH=/usr/lpp/mmfs/bin:${PATH}

ldapserver=directory01
filesystem=gpfs01
filesystemdir=/gpfs/${filesystem}
emailfile=${filesystemdir}/user.email
diskusagefile=${filesystemdir}/mmFilesetQuotaStatus.log
#tapequotafile=${filesystemdir}/tape.quota

# Mailing info
REPLYTO="rc-help@colorado.edu"
BCC=daniel.milroy@colorado.edu,pabi5658@colorado.edu,jonathon.anderson@colorado.edu
DATE=`date +"%B %Y"`

for project in `cat $emailfile | grep @ | grep -v ^# | awk '{print $1}'`; do
  # get quotas
  diskquota=`mmrepquota --block-size T -j $filesystem | grep "^${project} " | awk '{print $5}'` # in TB
  #inodequota=`mmrepquota --block-size G -j $filesystem | grep "^${project} " | awk '{print $12}'`
  # get current usage 
  diskusage_gb=`mmrepquota --block-size G -j $filesystem | grep "^${project} " | awk '{print $3}'`  # in GB
  diskusage=`echo "scale=3; ${diskusage_gb}/1000" | bc`  # in TB
  inodeusage=`mmrepquota --block-size G -j $filesystem | grep "^${project} " | awk '{print $9}'`
  # Get emails
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
  mail -s "/work/${project} Usage Report - ${DATE}" -r ${REPLYTO} -b $BCC $recipients << EOF

-- ${DATE} usage report for your CU PetaLibrary project named "${project}" --

Current disk space usage is ${diskusage} TB (out of your quota of ${diskquota} TB.)

The number of files and directories used is ${inodeusage}.

Users currently allowed filesystem access to the project are: ${users}

Reminder: Please acknowledge the PetaLibrary in any publications that were aided by its use.  A sample acknowledgement is at https://www.rc.colorado.edu/services/storage/petalibrary.  Also, remember that HIPAA, FERPA, ITAR, classified, or Personally-Identifiable data may not be stored on the PetaLibrary.

Please reply to this email if you have any questions.

Thanks,
Research Computing
EOF

done
