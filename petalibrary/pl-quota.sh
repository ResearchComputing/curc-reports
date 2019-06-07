#!/bin/bash

#Initially written on June 7, 2019
#

#error checking
if [ $# != 1 ]; then
echo ""
echo "This command returns the total and free disk"
echo "space for a PetaLibrary Active partition"
echo ""
echo "usage: ./pl-quota <spacename>"
echo ""
echo "for example, if your space is '/pl/active/COOL_LAB', type:"
echo "$ pl-quota COOL_LAB"
echo ""
exit 1
fi

#get total and free space from combo of beegfs-ctl and beegfs-df
TOTSPACE=$(beegfs-df -s $(beegfs-ctl --liststoragepools |grep $1 |awk '{ print $1}') |sed -n -e '/STORAGE/,$p' |grep GiB | awk '{ print $3}' | sed 's/GiB//g' | paste -sd+ - | bc)
FREESPACE=$(beegfs-df -s $(beegfs-ctl --liststoragepools |grep $1 |awk '{ print $1}') |sed -n -e '/STORAGE/,$p' |grep GiB | awk '{ print $4}' | sed 's/GiB//g' | paste -sd+ - | bc)

#compute percent free space
PCTFREE=$(echo "a=$FREESPACE/$TOTSPACE ; scale=1; a/0.01" | bc -l)

#report to user
echo ""
echo "Total_Space  |  Free_Space  |  %_Free_Space"
echo ${TOTSPACE} "GiB  | " ${FREESPACE} "GiB  |  " ${PCTFREE}\%
echo ""
