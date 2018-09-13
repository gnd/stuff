#!/bin/bash
#
# script to install wordpress
#
# Usage:
#
# run from the wordpress root dir
#
#
# gnd, 2015 - 2018
#############################################
# Set some globals
DATUM=`/bin/date +%D|sed 's/\//_/g'`
USER=`ls -la .|tail -1|awk {'print $3;'}`
GROUP=""

# Check if this is run as root
ROOT=`whoami`
if [[ $ROOT != "root" ]]; then
    echo "Please run as root"
    exit
fi

# Check if group set
if [[ -z $GROUP ]]; then
    echo "Please set the default GROUP variable"
    exit
fi

# Extract the latest version
wget https://wordpress.org/latest.tar.gz
tar -xzvf latest.tar.gz
cp -pr wordpress/* .

# Set permissions
echo "Setting ownership to $USER:$GROUP .."
chown $USER:$GROUP * -R
chmod 750 * -R
chmod 770 wp-content -R
chmod 750 wp-content/themes -R
chmod 750 wp-content/plugins -R
echo "done."

# Finish
echo "Cleaning up.."
rm -rf wordpress
rm latest.tar.gz
echo "done."

echo "Now access the admin and finish the install"
