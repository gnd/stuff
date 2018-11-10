#!/bin/bash
#
# === tnl.sh
# A bash script to maintain a SSH tunnel to access a local
# machine from internet via a shared server. This could be
# done with tinc or anything else but im just lazy to install
# additional stuff.
#
# It basically uses ssh pubkey auth on the server to forward
# a local port (22) to some remote port on the server. Later
# simply do on the server: ssh -p REMOTE_PORT localhost to access
# the local machine.
#
# To make this work add the following to .ssh/config of the user running this:
#
#	Host SERVER_NAME
#   controlmaster auto
#   controlpath ~/.ssh/SERVER_NAME.ctl
#
# Than generate a priv/pub keypair on the local machine and add the pubkey
# into .ssh/authorized_keys for the server user.
#
# Finally add sth like the following into ur crontab on the local machine:
#
#	# restart tunel every hour
#	5 */1 * * * SOME_USER PATH_TO/tnl.sh restart
#	# check if tunel running every 5m
#	*/5 * * * * SOME_USER PATH_TO/tnl.sh check
#
# 	(change the SOME_USER and PATH_TO to reflect your setup)
#
# gnd, 2016-2018
################################################################

# Set some params
SERVER_NAME=""
SERVER_USER=""
LOCAL_PORT="22"
REMOTE_PORT=""
CNTRL_PATH="~/.ssh/$SERVER_NAME.ctl"

# Check if params set
if [[ -z $SERVER_NAME ]]; then
	echo "Please provide a server name. Exiting."
	exit
fi
if [[ -z $SERVER_USER ]]; then
	echo "Please provide a server user. Exiting."
	exit
fi
if [[ -z $LOCAL_PORT ]]; then
	echo "Please provide a local port to be forwarded. Exiting."
	exit
fi
if [[ -z $REMOTE_PORT ]]; then
	echo "Please provide a remote port to forward to. Exiting."
	exit
fi

case "$1" in
	'check')
		count=`ps -ef|grep "ssh -o"|grep -v grep|wc -l`
		if [ $count -gt 1 ]; then
			echo "Running more times: $count"
			for pid in `ps -ef|grep "ssh -o"|grep -v grep|awk {'print $2;'}`
			do
				echo "Shutting down $pid"
				kill -9 $pid
			done
			rm $CNTRL_PATH
		fi
		sts=`ssh -O check $SERVER_NAME 2>&1|awk {'print $2;'}`
		if [ "$sts" != "running" ]
		then
			echo "trying to start"
			ssh -o ConnectTimeout=10 -l $SERVER_USER -f -N -M -R $REMOTE_PORT:127.0.0.1:$LOCAL_PORT $SERVER_NAME
		else
			echo $sts
		fi
	;;
	'start')
		ssh -o ConnectTimeout=10 -l $SERVER_USER -f -N -M -R $REMOTE_PORT:127.0.0.1:$LOCAL_PORT $SERVER_NAME
	;;
	'stop')
		ssh -T -O "exit" $SERVER_NAME
		rm $CNTRL_PATH
	;;
	'restart')
		sts=`ssh -O check $SERVER_NAME 2>&1|awk {'print $2;'}`
		if [ "$sts" == "running" ]
		then
			pid=`ssh -O check $SERVER_NAME 2>&1|awk {'print $3;'}|sed 's/)//g'|sed 's/(pid=//g'`
			echo "$sts: $pid"
			ssh -T -O "exit" $SERVER_NAME
			sleep 1
			echo "killing $pid"
			kill -9 "$pid"
		fi
		rm $CNTRL_PATH
		echo "starting"
		ssh -o ConnectTimeout=10 -l $SERVER_USER -f -N -M -R $REMOTE_PORT:127.0.0.1:$LOCAL_PORT $SERVER_NAME
	;;
	*)
		echo "Usage: $0 [check|start|stop|restart]"
	;;
esac
