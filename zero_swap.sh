#!/bin/bash
#
# zero swap to prevent swap digging
# see: http://blog.sevagas.com/?Digging-passwords-in-Linux-swap
#
# make really sure $SWAP is set correctly lol
#
# gnd @ gnd.sk, 202
##############################################

# set some globals
SWAP="" # could be also for SWAP in `cat /proc/swaps|grep -v Filename`; do

usage() {
	printf "\n"
	printf "Set SWAP variable and run like:\n"
	printf "$0 \n\n"
}

# check if parameter given
if [[ -z $SWAP ]]; then
	usage
	exit
fi

# swapoff, zero, mkswap & swapon
swapoff $SWAP
dd if=/dev/zero of=$SWAP bs=512
mkswap $SWAP
swapon $SWAP
