#!/bin/bash
# Simple disk usage monitoring with mail notification
# 2009-2020, gnd@gnd.sk
#########################################

# Reporting config parameters
SERVER=""
PORT=""
USER=""
PASS=""
FROM=""
TO=""

# Monitoring config parameters
BOX=""
ALARM_THRESHOLD=90
declare -a DISKS=(/dev/mapper/cloudcontainer--vg-root /dev/sda)

# Check disk usage
for DISK in ${DISKS[@]};
do
    LINE1=`df -h $DISK|grep Used`
    LINE2=`df -h $DISK|grep -v Used`
    USAGE=`df $DISK|grep -v Use|awk {'print $5;'}|sed s/%//g`
    if [ $USAGE -gt $ALARM_THRESHOLD ]
    then
        message="$LINE1\r\n$LINE2"
        sendemail -o tls=yes -s $SERVER:$PORT -xu $USER -xp $PASS -f $FROM -t $TO -u "WARNING: $DISK over $ALARM_THRESHOLD% on $BOX" -m "$message"
    fi
done
