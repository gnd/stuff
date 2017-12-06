#!/bin/bash
#
# create, encrypt & store www backups
#
# gnd @ gnd.sk, 2009 - 2017
##############################################

# set some globals
DATUM=`date +%D|sed 's/\//_/g'`
WWW_DIR=""
LOCAL_DIR=""
GPG_RCPT=""
RETENTION_DAYS=30

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
for f in `find $LOCAL_DIR -type f -name "www_*.gpg" -mtime +$RETENTION_DAYS`
do
        rm $f
done

# do the backup
now=`date +"%D %H:%M"`
echo ""
echo "--- $now Backup starting .."

# dump & encrypt single databases
for DOMAIN in `ls $WWW_DIR`
do
        echo "Packing $DOMAIN .."
        nice tar -cf $LOCAL_DIR/$DOMAIN"_"$DATUM.tar $WWW_DIR/$DOMAIN
	chmod 600 $LOCAL_DIR/$DOMAIN"_"$DATUM.tar
        echo "Encrypting $DOMAIN .."
	nice gpg -r "$GPG_RCPT" --output $LOCAL_DIR"/www_"$DOMAIN"_"$DATUM".gpg" --encrypt $LOCAL_DIR/$DOMAIN"_"$DATUM".tar"
	chmod 600 $LOCAL_DIR"/www_"$DOMAIN"_"$DATUM".gpg"
	echo "Deleting plaintext for $DOMAIN .."
        rm $LOCAL_DIR/$DOMAIN"_"$DATUM".tar"
done

# transfer to remote
if [[ $REMOTE -eq "1" ]]; then
        echo "Transferring to $REMOTE_HOST .."
        rsync -ravhP $LOCAL_DIR"/www_*.gpg" $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR
fi

# clean after
if [[ $DELETE_LOCAL -eq "1" ]]; then
	echo "Cleaning up .."
	rm $LOCAL_DIR"/www_*.gpg"
fi

# finish
now=`date +"%D %H:%M"`
echo "--- $now Backup finished"