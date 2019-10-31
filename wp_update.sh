#!/bin/bash
#
# Script to insta-update wordpress
#
# Usage:
#   run from the wordpress root dir
#
# gnd, 2015 - 2019
#############################################

# Check if this is run as root
ROOT=`whoami`
if [[ $ROOT != "root" ]]; then
    echo "Please run as root"
    exit
fi

# Set some globals
DATUM=`/bin/date +%D|sed 's/\//_/g'`
USER=`ls -la wp-config.php|awk {'print $3;'}`
GROUP=`ls -la wp-config.php|awk {'print $4;'}`

# Backup the previous version
echo "backing up.."
tar -cf "../preupdate_"$DATUM".tar" .
chmod 000 "../preupdate_"$DATUM".tar"
echo "done."

# Delete previous version
echo "deleting old files .."
cp wp-config.php /root/wp-config-old.php
rm *
rm -rf wp-admin/
rm -rf wp-includes/
echo "done."

# Download the latest version
sleep 2
wget https://wordpress.org/latest.tar.gz
tar -xzvf latest.tar.gz
sleep 2

# Overwrite files
echo "replacing files .."
cp wordpress/* .
rm wp-config*
cp -pr wordpress/wp-admin .
cp -pr wordpress/wp-includes .
cp -pr wordpress/wp-content/* wp-content/
cp /root/wp-config-old.php wp-config.php
rm /root/wp-config-old.php
echo "done."

# Set permissions
echo "Setting ownership to $USER:$GROUP .."
chown $USER:$GROUP * -R
chmod 750 * -R
chmod 770 wp-content -R
chmod 750 wp-content/themes -R
chmod 770 wp-content/plugins -R
chmod g+s wp-content/plugins -R
echo "done."

# Prohibit file edit via WP
RES=`cat wp-config.php|grep DISALLOW_FILE_EDIT|wc -l`
if [[ $RES -gt 0 ]]; then
    echo "DISALLOW_FILE_EDIT already set."
else
    echo "Modifying config (DISALLOW_FILE_EDIT) .."
    echo "" >> wp-config.php
    echo "# Disallowing file editing via WP (gnd, $DATUM)" >> wp-config.php
    echo "define('DISALLOW_FILE_EDIT', true);" >> wp-config.php
    echo "done."
fi

# Make WP access sisk straight
RES=`cat wp-config.php|grep FS_METHOD|wc -l`
if [[ $RES -gt 0 ]]; then
    echo "FS_METHOD already set."
else
    echo "Modifying config (FS_METHOD) .."
    echo "" >> wp-config.php
    echo "# Makes WP access disk straight (not via FTP) (gnd, $DATUM)" >> wp-config.php
    echo "define('FS_METHOD', 'direct');" >> wp-config.php
    echo "done."
fi

# Leave a note in the wp-config
echo "" >> wp-config.php
echo "# WP last updated by gnd on $DATUM" >> wp-config.php

# Finish
echo "Cleaning up.."
rm -rf wordpress
rm latest.tar.gz
echo "done."

echo "Now access the admin and finish the update"
