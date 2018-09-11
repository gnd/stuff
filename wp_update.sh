#!/bin/bash
#
# script to insta-update wordpress
#
# Usage:
#
# run from the wordpress root dir
#
#
# gnd, 2015 - 2018
#############################################
DATUM=`/bin/date +%D|sed 's/\//_/g'`
USER=`ls -la wp-config.php|awk {'print $3;'}`
GROUP=`ls -la wp-config.php|awk {'print $4;'}`

echo "backing up.."
tar -cf "../preupdate_"$DATUM".tar" .
chmod 000 "../preupdate_"$DATUM".tar"
echo "done."

echo "deleting old files .."
cp wp-config.php /root/wp-config-old.php
rm *
rm -rf wp-admin/
rm -rf wp-includes/
echo "done."

sleep 2
wget https://wordpress.org/latest.tar.gz
tar -xzvf latest.tar.gz
sleep 2

echo "replacing files .."
cp wordpress/* .
rm wp-config*
cp -pr wordpress/wp-admin .
cp -pr wordpress/wp-includes .
cp -pr wordpress/wp-content/* wp-content/
cp /root/wp-config-old.php wp-config.php
rm /root/wp-config-old.php
echo "done."

echo "Setting ownership to $USER:$GROUP .."
chown $USER:$GROUP * -R
chmod 750 * -R
chmod 770 wp-content -R
chmod 750 wp-content/themes -R
chmod 750 wp-content/plugins -R
echo "done."

echo "Modifying config (DISALLOW_FILE_EDIT .."
echo "define('DISALLOW_FILE_EDIT', true);" >> wp-config.php
echo "done."

echo "Cleaning up.."
rm -rf wordpress
rm latest.tar.gz
echo "done."

echo "Now access the admin and finish the update"
