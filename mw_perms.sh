#!/bin/bash
#
# This sets permissions for mediawiki installs
#
# gnd, 2019
##############################################

# check input
if [[ -z $1 ]]; then
        echo "Please provide a mediawiki directory"
        exit
else
        if [[ ! -d $1 ]]; then
                echo "No such directory"
                exit
        else
                dir=$1
        fi
fi

# set perms
chown www-data:www-data $dir -R
chmod o-rwx $dir -R
chmod ug-w $dir -R
chmod ug+w $dir/images -R

# done
echo "done"
