#!/bin/bash
#
# create, encrypt & store mysql db backups
#
# gnd @ gnd.sk, 2009 - 2017
##############################################

# set some globals
DATUM=`date +%D|sed 's/\//_/g'`
LOCAL_DIR=""
GPG_RCPT=""
RETENTION_DAYS=30

# db server conf
DB_HOST=""
DB_PASS=""
DB_USER=""

# if using a remote server for backup storage
REMOTE=0
REMOTE_USER=""
REMOTE_HOST=""
REMOTE_DIR=""
DELETE_LOCAL=0

# check if GPG_RCPT set
GPG_LINES=`gpg --list-keys|grep "$GPG_RCPT"|wc -l`
if [[ $GPG_LINES != "1" ]]; then
	echo "Please provide a gpg recipient"
	exit
fi

# delete files older then RETENTION_DAYS
for f in `find $LOCAL_DIR -type f -name "sql_*.gpg" -mtime +$RETENTION_DAYS`
do
        rm $f
done

# do the backup
now=`date +"%D %H:%M"`
echo ""
echo "--- $now Backup starting .."

# dump & encrypt single databases
for DB_NAME in `mysql -u $DB_USER -h $DB_HOST -p$DB_PASS -e "show databases"|grep -v "+"|grep -v "Database"|grep -v information_schema|grep -v performance_schema`
do
        echo "Dumping $DB_NAME .."
        mysqldump --skip-extended-insert --skip-set-charset -u $DB_USER -h $DB_HOST -p$DB_PASS $DB_NAME --result-file=$LOCAL_DIR/$DB_NAME.sql
	chmod 600 $LOCAL_DIR/$DB_NAME.sql
        echo "Encrypting $DB_NAME .."
        gpg -r "$GPG_RCPT" --output $LOCAL_DIR"/sql_"$DB_NAME"_"$DATUM".gpg" --encrypt $LOCAL_DIR/$DB_NAME.sql
	chmod 600 $LOCAL_DIR"/sql_"$DB_NAME"_"$DATUM".gpg"
	echo "Deleting plaintext for $DB_NAME .."
        rm $LOCAL_DIR/$DB_NAME.sql
done

# transfer to remote
if [[ $REMOTE -eq "1" ]]; then
        echo "Transferring to $REMOTE_HOST .."
        rsync -ravhP $LOCAL_DIR"/sql_*.gpg" $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR
fi

# clean after
if [[ $DELETE_LOCAL -eq "1" ]]; then
	echo "Cleaning up .."
	rm $LOCAL_DIR"/sql_*.gpg"
fi

# finish
now=`date +"%D %H:%M"`
echo "--- $now Backup finished"