#!/usr/bin/python
#
# used to decode partially hex-obfuscated php shells
# gnd, 2017
####################################################

import os
import sys

# check if all arguments
if (len(sys.argv) < 2):
    print "Usage: dechex.py <file_name>"
    sys.exit(0)

# check if file exists
encfile = sys.argv[1]
if ( not os.path.isfile(encfile)):
    print "File %s does not exist" % encfile
else:
    f = file(encfile, 'r')
    k = f.read()
    f.close()

# decode hex parts of the file
print "Decoding .."
dec=""
i=0
while (i < len(k)):
    if (k[i] == '\\'):
        if(k[i+1] == 'x'):
            # skip some chars
            if ((k[i+3] == '\\') & (k[i+2] in arr)):
                dec+=' '
                i+=3
            else:
                a = k[i:i+4]
                dec+=a.replace('\\x','').decode('hex')
                i+=4
        else:
            dec+=k[i]
            i+=1
    else:
        dec+=k[i]
        i+=1

# write decoded file into file_name.dec
decfile = encfile + ".dec"
f = file(decfile, 'w') # will overwrite
f.write(dec)
f.close()

print "Done !"
