#!/bin/bash
#
# export mysql dbs for export
#
# gnd @ gnd.sk, 2009 - 2018
##############################################

# set some globals
DATUM=`date +%D|sed 's/\//_/g'`
LOCAL_DIR=""
DUMP_USERS=""

# db server conf
DB_HOST=""
DB_PASS=""
DB_USER=""

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

# dump & encrypt single databases
for DB_NAME in `mysql -u $DB_USER -h $DB_HOST -p$DB_PASS -e "show databases"|grep -v "+"|grep -v "Database"|grep -v information_schema|grep -v performance_schema`
do
	echo "Dumping $DB_NAME .."
	mysqldump --skip-extended-insert --skip-set-charset -u $DB_USER -h $DB_HOST -p$DB_PASS $DB_NAME --result-file=$LOCAL_DIR/$DB_NAME.sql

	# transfer to remote
	if [[ $DUMP_USERS -eq "1" ]]; then
		$USER_NAME = `mysql -u $DB_USER -h $DB_HOST -p$DB_PASS -e "use mysql; select User from db where Db = '$DB_NAME'"`
		$USER_PASS = `mysql -u $DB_USER -h $DB_HOST -p$DB_PASS -e "use mysql; select Password from user where User = '$USER_NAME'"`
		echo "$USER_NAME $USER_PASS"> $LOCAL_DIR/$DB_NAME.txt
	fi
done
