#!/usr/bin/python
#
# used to decode partially hex-obfuscated php shells
# gnd, 2017
####################################################

import os
import re
import sys

# set some globals
search = False
arr = ['0','1','2','3','4','5','6','7','8','9','0','a','b','c','d','e','f']

# check if all arguments
if (len(sys.argv) < 2):
    print "Usage: decode_hex.py <file_name>"
    print "Usage: decode_hex.py [-l] ['pattern'] ['regexp pattern'] <file_name>"
    sys.exit(0)

# process input args
if (sys.argv[1] == "-l"):
    search = True
    p1 = sys.argv[2].strip("'")
    p2 = sys.argv[3].strip("'")
    encfile = sys.argv[4]
else:
    encfile = sys.argv[1]

# check if encfile exists
if ( not os.path.isfile(encfile)):
    print "File %s does not exist" % encfile
else:
    f = file(encfile, 'r')
    k = f.read()
    f.close()

# decode hex parts of the file
if not search:
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
                dec+=k[i:i+4].replace('\\x','').decode('hex')
                i+=4
        else:
            dec+=k[i]
            i+=1
    else:
        dec+=k[i]
        i+=1

# search for patterns
if search:
    if (p1 in dec) & bool(re.search(p2,dec)):
        print encfile
        sys.exit(0)

# .. or just output decoded file
else:
    # write decoded file into file_name.dec
    decfile = encfile + ".dec"
    f = file(decfile, 'w') # will overwrite
    f.write(dec)
    f.close()
    print "Done !"