#!/bin/bash
#
# create opendkim keys & settings for a domain
#
# gnd @ gnd.sk, 2018
##############################################

usage() {
	printf "\n"
	printf "Usage: \n"
	printf "$0 <domain.tld (eg. $0 example.com)> \n\n"
}

# Check if this is run as root
ROOT=`whoami`
if [[ $ROOT != "root" ]]; then
    echo "Please run as root"
    exit 1
fi

# Set some globals
ODKIMDIR='/etc/opendkim'
USER=`opendkim`
GROUP=`opendkim`

# Check if params set
if [[ -z $1 ]]; then
    usage
	echo "No domain provided. Exiting"
	exit
else
    DOMAIN=$1
fi

# Generate keys and config entries
mkdir -p $ODKIMDIR/keys/$DOMAIN
opendkim-genkey -D $ODKIMDIR/keys/$DOMAIN -d $DOMAIN -s mail
chown opendkim:opendkim $ODKIMDIR/keys/$DOMAIN -R
echo "mail._domainkey.$DOMAIN $DOMAIN:mail:$ODKIMDIR/keys/$DOMAIN/mail.private" >> $ODKIMDIR/KeyTable
echo "*@$DOMAIN mail._domainkey.$DOMAIN" >> $ODKIMDIR/SigningTable
service opendkim restart

# Output the dkim pubkey
echo "Done ! Use this as a TXT record for mail._domainkey.$DOMAIN:"
cat $ODKIMDIR/keys/$DOMAIN/mail.txt

# Exit
exit 0
