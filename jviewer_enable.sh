#!/bin/bash
#
#
# This script prepares java.policy and java.security files so that the
# ThinkServer System Manager console can be run on Linux with javaws
#
# First icedtea-netx package needs to be installed:
# apt-get install icedtea-netx
#
# When installed download the jviewer.jnlp and run this script
# After the console is closed, the changes will be reverted
#
# gnd, 2018
########################################################################

# Check if this is run as root
ROOT=`whoami`
if [[ $ROOT != "root" ]]; then
    echo "Please run as root"
    exit
fi

# Get openjdk version first
VER=`dpkg -la|grep openjdk|head -1|awk {'print $2;'}|sed 's/openjdk-//g' |sed 's/-jre.*//g'`

# Update java.policy - check if not already done
POLICY_UPDATED=`cat /etc/java-$VER-openjdk/security/java.policy|grep jnviewer-insert|wc -l`
if [[ "$POLICY_UPDATED" -gt 0 ]]; then
    echo "The file /etc/java-$VER-openjdk/security/java.policy seems to be already updated."
    exit
fi

# Update java.policy now
echo "Updating java.policy .."
RND=`openssl rand -hex 2`
TMPFILE="/tmp/pol_"$RND
cp /etc/java-$VER-openjdk/security/java.policy /tmp/java.policy
echo "// jviewer-insert-start" > $TMPFILE
echo "grant {" >> $TMPFILE
echo 'permission java.io.FilePermission "/usr/bin/xprop", "execute";' >> $TMPFILE
echo "permission java.security.AllPermission;" >> $TMPFILE
echo "};" >> $TMPFILE
echo "// jviewer-insert-end" >> $TMPFILE
cat $TMPFILE > /etc/java-$VER-openjdk/security/java.policy
cat /tmp/java.policy >> /etc/java-$VER-openjdk/security/java.policy
rm $TMPFILE
echo ".. java.policy updated"

# Update java.security - check if not already done
SECURITY_UPDATED=`cat /etc/java-$VER-openjdk/security/java.security|grep jnviewer-insert|wc -l`
if [[ "$SECURITY_UDPATED" -gt 0 ]]; then
    echo "The file /etc/java-$VER-openjdk/security/java.security seems to be already updated."
    exit
fi

# Update java.security now
echo "Updating java.security .."
RND=`openssl rand -hex 2`
TMPFILE="/tmp/sec_"$RND
cp /etc/java-$VER-openjdk/security/java.security /tmp/java.security
cp /etc/java-$VER-openjdk/security/java.security $TMPFILE
sed -i '/jdk.jar.disabledAlgorithms/i # jviewer-insert-start' $TMPFILE
sed -i '/jdk.jar.disabledAlgorithms/a # jviewer-insert-end' $TMPFILE
sed -i 's/jdk.jar.disabledAlgorithms/# jdk.jar.disabledAlgorithms/g' $TMPFILE
mv $TMPFILE /etc/java-$VER-openjdk/security/java.security
echo ".. java.security updated"

# Launch jnviewer
read -p "Please provide path to jviewer.jnlp: " JNPATH
if [ ! -f "$JNPATH/jviewer.jnlp" ]; then
    echo "File not found!"
    read -p "Please provide path to jviewer.jnlp: " JNPATH
    if [ ! -f "$JNPATH/jviewer.jnlp" ]; then
        echo "File not found. Will revert changes."
    else
        javaws -verbose $JNPATH/jviewer.jnlp
    fi
else
    javaws -verbose $JNPATH/jviewer.jnlp
fi

# Remove changes from java.policy
echo "Removing changes to java.policy .."
sed -i '/jviewer-insert-start/,/jviewer-insert-end/{//!d}' /etc/java-$VER-openjdk/security/java.policy
sed -i '/\/\/ jviewer-insert-start/d' /etc/java-$VER-openjdk/security/java.policy
sed -i '/\/\/ jviewer-insert-end/d' /etc/java-$VER-openjdk/security/java.policy
echo ".. java.policy updated"

# Remove changes from java.security
echo "Removing changes to java.security .."
sed -i 's/# jdk.jar.disabledAlgorithms/jdk.jar.disabledAlgorithms/g' /etc/java-$VER-openjdk/security/java.security
sed -i '/# jviewer-insert-start/d' /etc/java-$VER-openjdk/security/java.security
sed -i '/# jviewer-insert-end/d' /etc/java-$VER-openjdk/security/java.security
echo ".. java.security updated"
