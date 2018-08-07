#!/bin/bash
#
# import mysql dbs during a migration
#
# gnd @ gnd.sk, 2009 - 2018
##############################################

# set some globals
DATUM=`date +%D|sed 's/\//_/g'`
LOCAL_DIR=""
DROP_DBS=""
IMPORT_CREDS=""

# db server conf
DB_HOST=""
DB_PASS=""
DB_USER=""

# check if this is run as root
ROOT=`whoami`
if [[ $ROOT != "root" ]]; then
    echo "Please run as root."
    exit
fi

# check if params set
if [[ -z $LOCAL_DIR ]]; then
	echo "Please provide a local dir path. Exiting."
	exit
fi
if [[ -z $DB_HOST ]]; then
	echo "Please provide a db hostname. Exiting."
	exit
fi
if [[ -z $DB_PASS ]]; then
	echo "Please provide a db password. Exiting."
	exit
fi
if [[ -z $DB_USER ]]; then
	echo "Please provide a db username. Exiting."
	exit
fi

# check if user really wants to drop dbs
if [[ $DROP_DBS -eq "1" ]]; then
    read -p "Do you really want to drop all dbs before importing ? [yes/no]: " $ANS
    if [[ $ANS != "yes" ]]; then
        DROP_DBS=0
    fi
fi

# dump single databases
for DB_DUMP in `ls $LOCAL_DIR|grep sql`
do
    DB_NAME=`echo $DB_DUMP|sed 's/\.sql//g'`

    # this will drop former dbs before importing
    if [[ $DROP_DBS -eq "1" ]]; then
        echo "Dropping db $DB_NAME .."
        mysql -u $DB_USER -h $DB_HOST -p$DB_PASS -e "DROP DATABASE $DB_NAME"
    fi

	echo "Importing db from $DB_DUMP .."
    mysql -u $DB_USER -h $DB_HOST -p$DB_PASS -e "CREATE DATABASE $DB_NAME CHARACTER SET utf8 COLLATE utf8_general_ci"
	mysql -u $DB_USER -h $DB_HOST -p$DB_PASS $DB_NAME < $LOCAL_DIR/$DB_DUMP

    # this will also import user credentials
    if [[ $IMPORT_CREDS -eq "1" ]]; then
        echo "Setting user credentials for $DB_NAME .."
        DUMP_USER=`cat $LOCAL_DIR/$DB_NAME.txt|awk {'print $1;'}`
        DUMP_HASH=`cat $LOCAL_DIR/$DB_NAME.txt|awk {'print $2;'}`
        mysql -u $DB_USER -h $DB_HOST -p$DB_PASS -e "GRANT ALL ON $DB_NAME.* to '$DUMP_USER'@'localhost' IDENTIFIED BY PASSWORD '$DUMP_HASH'"
        mysql -u $DB_USER -h $DB_HOST -p$DB_PASS -e "FLUSH PRIVILEGES"
    fi

    echo "Database $DB_NAME imported."
done
