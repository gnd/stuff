#!/bin/bash
#
# make wordpress belong to the ftp user,
# to be able to update via web interface
#
# Usage:
#
# run from the user's FTP root:
#   wp_own.sh <site_name>
#
# gnd @ gnd.sk, 2013 - 2018
#############################################

usage() {
	printf "\n"
	printf "Usage: \n"
	printf "$0 <port PORT |name NAME |ip IP |iface IFACE> \n\n"
}

# check if parameter given
if [[ -z $1 ]]; then
	usage
	exit
fi

# process input
SITE=$1
USER=`ls -la .|head -2|tail -1|awk {'print $3;'}`

# set rights (we dont care about webserver here - this is up to the admin)
chown $USER $SITE -R
chmod u+rwx -R

# check wp-config for FTP_BASE setting & change it
FTBASE=`grep FTP_BASE $SITE/wp-config.php |wc -l`
if [ "$FTBASE" -eq "0" ]
then
        echo "zero FTP_BASE"
        sed -i "17a\define('FTP_BASE', '/$SITE/');" $SITE/wp-config.php
fi
if [ "$FTBASE" -eq "1" ]
then
        echo "one FTP_BASE"
        sed -i "s/FTP_BASE'/FTP_BASE', '\/$SITE\/');\n\/\/ gnd change/g" $SITE/wp-config.php
fi

# done
echo "FTP_BASE set to: $SITE"
