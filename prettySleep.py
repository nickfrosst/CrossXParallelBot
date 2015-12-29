from __future__ import division
import time
import sys

def pretty_sleep(t):
    length = 40
    for i in range(0,t):
        p = int(i/t * length)
        prgrs = "=" * (p)  + "." * (length-p)
        print '{0}\r'.format("sleeping for " + str(t) + " seconds - ["  + prgrs + "]"),
        time.sleep(1)
        sys.stdout.flush()
    print
