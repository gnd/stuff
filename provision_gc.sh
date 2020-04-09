#!/bin/sh
#
# creates a new freebsd instance on gcloud compute and sets it up
# gnd, 2020
#################################################################

# some globals
TYPE="g1-small"
IMAGE="freebsd-12-1-release-amd64"
SIZE="30"
PUBKEY="" #/home/gnd/.ssh/tpd.pub
KEY=`echo $PUBKEY|sed 's/\.pub//g'`

# check if PUBKEY specified
if [ -z $PUBKEY ]; then
    echo "Plz edit this script and specify a path to your public key in PUBKEY or generate one for this task and specify its path"
    exit 1
else
    ACTION=$1
fi

# get action
if [ -z $1 ]; then
    echo "Plz provide action"
    echo "Usage: $0 [new_instance | setup_instance] <instance_name>"
    exit 1
else
    ACTION=$1
fi

# get instance name
if [ -z $2 ]; then
    echo "Plz provide instance_name"
    exit 1
else
    NAME=$2
fi

rdo() {
    CMD="sudo $2"
    ssh -i $KEY $1 $CMD
}

# zone setup
gcloud compute project-info add-metadata --metadata google-compute-default-region=europe-west1,google-compute-default-zone=europe-west1-b
gcloud config set compute/zone europe-west1-b
export CLOUDSDK_COMPUTE_ZONE="europe-west1-b"

# get a new instance to play with
if [ "$ACTION" = "new_instance" ]; then
    # instance setup
    echo "Creating instance"
    gcloud compute instances create $NAME --machine-type $TYPE --network "default" --maintenance-policy "MIGRATE" --image $IMAGE --image-project=freebsd-org-cloud-dev --boot-disk-size $SIZE --tags=gndtask001
    # no matter how we setup initial zones, this still requires that we specify a zone
    echo "Creating extra disk"
    gcloud compute disks create $NAME-da1 --size 20G --zone=europe-west1-b
    echo "Attaching disk to instance"
    gcloud compute instances attach-disk $NAME --disk=$NAME-da1
    # am not able to attach my pubkey to the machine like this: gcloud compute instances add-metadata $NAME --metadata-from-file ssh-keys=$PUBKEY
    # so lets just do it by hand. i guess playing around with osLogin in gcloud compute would solve the issue
    echo ""
    echo "\033[1mInstance $NAME ready.\033[0m Add contents of $PUBKEY into authorized_keys on the instance and run $0 setup_instance $NAME"
    #gcloud compute ssh $NAME
fi

if [ "$ACTION" = "setup_instance" ]; then
    # get machine ip
    IP=`gcloud compute instances list|grep $NAME|awk {'print $5;'}`
    IP_INTERNAL=`gcloud compute instances list|grep $NAME|awk {'print $4;'}`
    echo "Instance IP: $IP INTERNAL: $IP_INTERNAL"

    # system setup
    echo "Creating zpool2"
    rdo $IP 'zpool create zpool2 da1'
    echo "Creating zpool2/jail dataset in /jail"
    rdo $IP 'zfs create -o mountpoint=/jail zpool2/jail'
    echo "Creating zpool2/jail/web dataset in /jail/web"
    rdo $IP 'zfs create -o mountpoint=/jail/web zpool2/jail/web'
    echo "Fetching 12.1 base"
    rdo $IP 'fetch http://ftp.freebsd.org/pub/FreeBSD/releases/amd64/12.1-RELEASE/base.txz'
    echo "Extracting base.txz to /jail/web"
    rdo $IP 'tar -xf base.txz -C /jail/web'
    echo "Updating FreeBSD in /jail/web"
    rdo $IP 'freebsd-update --not-running-from-cron -b /jail/web fetch install'
    echo "Setting some params in /etc/rc.conf"
    ssh -i $KEY $IP 'sudo sh -c "echo \"zfs_enable=YES\" >> /etc/rc.conf"'
    ssh -i $KEY $IP 'sudo sh -c "echo \"jail_enable=YES\" >> /etc/rc.conf"'
    ssh -i $KEY $IP 'sudo sh -c "echo \"pf_enable=YES\" >> /etc/rc.conf"'
    ssh -i $KEY $IP 'sudo sh -c "echo \"cloned_interfaces=lo1\" >> /etc/rc.conf"'
    echo "Creating cloned interface"
    rdo $IP 'service netif cloneup'
    echo "Setting up NAT"
    line="nat pass on vtnet0 from 127.0.1.1 to any -> $IP_INTERNAL"
    ssh -i $KEY $IP "sudo sh -c 'echo \"$line\" > /etc/pf.conf'"
    line="rdr pass on vtnet0 proto tcp from any to $IP_INTERNAL port {http} -> 127.0.1.1"
    ssh -i $KEY $IP "sudo sh -c 'echo \"$line\" >> /etc/pf.conf'"
    rdo $IP 'service pf start'

    # setup jail
    echo "Setting up jail.conf"
    TMP=`mktemp`
    TMP_BASE=`basename $TMP`
    echo 'exec.start = "/bin/sh /etc/rc";
    exec.stop = "/bin/sh /etc/rc.shutdown";
    exec.clean;
    mount.devfs;
    allow.raw_sockets;

    web {
        host.hostname = "web.domain.local";
        path = "/jail/web";
        ip4.addr = "lo1|127.0.1.1/32";
    }' > $TMP
    scp -i $KEY $TMP gnd@$IP:./
    rdo $IP "mv $TMP_BASE /etc/jail.conf"
    ssh -i $KEY $IP 'sudo sh -c "echo \"hostname=web\" > /jail/web/etc/rc.conf"'
    ssh -i $KEY $IP 'sudo sh -c "echo \"nameserver 169.254.169.254\" > /jail/web/etc/resolv.conf"'
    rdo $IP 'service jail start web'

    # make web great again
    echo "Installing packages into jail"
    rdo $IP 'jexec web pkg install --yes apache24 mod_php74'
    echo "Enabling Apache on boot"
    ssh -i $KEY $IP 'sudo sh -c "echo \"apache24_enable=YES\" >> /jail/web/etc/rc.conf"'
    echo "Enabling mod php"
    TMP=`mktemp`
    TMP_BASE=`basename $TMP`
    echo 'DirectoryIndex index.php

    <FilesMatch "\.php$">
    	SetHandler application/x-httpd-php
    </FilesMatch>

    # lol
    <Files my-info>
       SetHandler application/x-httpd-php
    </Files>' > $TMP
    scp -i $KEY $TMP gnd@$IP:./
    rdo $IP "mv $TMP_BASE /jail/web/usr/local/etc/apache24/Includes/php.conf"
    echo "Adding phpinfo()"
    ssh -i $KEY $IP 'sudo sh -c "echo \"<?php phpinfo(); ?>\" > /jail/web/usr/local/www/apache24/data/my-info"'
    echo "Starting Apache"
    rdo $IP 'jexec web service apache24 start'

    echo "Open port 80 for target-tags gndtask001"
    gcloud compute firewall-rules create allow-gndtask001-80 --allow tcp:80 --target-tags=gndtask001
    echo ""
    echo "\033[1mDone.\033[0m phpinfo() available at http://$IP/my-info"
fi
