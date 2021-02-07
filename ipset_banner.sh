#!/bin/sh
#
# Emergency script to ban botnet bruteforce attempts (ipset version) for limited time
# See https://kirkkosinski.com/2013/11/mass-blocking-evil-ip-addresses-iptables-ip-sets/
#
# Run this from cron every N minutes and adjust LOG_HITS and LOG_LINES accordingly
#
# gnd, 2015-2021
#########################################################################################

LOG_HITS=20
LOG_LINES=100000
BAN_TIME=480
LOG_FILE=""

# ipset setup
BANNED_DIR=""
WHITELIST=""

# temp files
TMPFILE=`mktemp`
NEWIPS=`mktemp`

# tail access log, find all POSTs to login, sort & count & show IPs which tried more than $LOG_HITS times
# wordpress login version
for IP in `tail -$LOG_LINES $LOG_FILE |grep POST | grep wp-login |awk {'print $2;'} | sort | uniq -c | sort -n | awk '{ if ($1 > $LOG_HITS) print $2 }'`
do
	touch $BANNED_DIR"/"$k
done

# delete banned ips older than 8hrs
find $BANNED_DIR -type f -mmin +$BAN_TIME -exec rm {} \;

# create new list 
for k in `ls $BANNED_DIR`
do
	echo $k >> $TMPFILE
done

# subtract IPs in whitelist from all banned ips
grep -vxFf $WHITELIST $TMPFILE > $NEWIPS 

# ipset all NEWIPs as "banned_ips" effectively banning them immediately without firewall reload
for IP in `cat $NEWIPS`; do
	ipset add banned_ips $IP
done

# small reporting
ALL=`wc -l $NEWIPS|awk {'print $1;'}`
echo "There is a total of $ALL banned IPs." 

# cleanup
rm $TMPFILE
rm $NEWIPS
