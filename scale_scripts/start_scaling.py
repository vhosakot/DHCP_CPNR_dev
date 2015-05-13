#! /usr/bin/python

import os
import time

for i in range(0, 100):
    logfile = str((i+1) * 100) + ".log"
    cmd = "./port_scale_wrapper.py 100 -pc 0 -nc 0 &> " + logfile
    print cmd
    os.system(cmd)
    time.sleep(5)
