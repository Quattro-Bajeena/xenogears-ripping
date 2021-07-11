#!/usr/bin/env python
# Turn a file of 2352 byte sectors into one of 2048 byte sectors.

import sys

if len(sys.argv) < 3:
    print('usage: naiverip.py in out')
    sys.exit(1)

secsize = 2352

fin = open(sys.argv[1],'rb')
fout = open(sys.argv[2],'wb')
while True:
    rd = fin.read(secsize)
    if len(rd) < secsize:
        break
    fout.write(rd[24:2048+24])


fout.close()