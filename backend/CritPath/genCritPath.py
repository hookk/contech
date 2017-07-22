#!/usr/bin/env python

import os
import sys
import argparse
sys.path.append(os.path.join(os.environ["CONTECH_HOME"], "scripts"))
import util
import subprocess
import shutil
import re
from array import array

# given a directory (or directories) from dynamic analysis, generate the crit path file
#  Format: (all numbers are in binary, speedups are 4byte floats, 
#           configs, bottlenecks are 2 byte ints, others are 4 byte ints)
#    <number of configurations>-<number of tasks>
#    <context ID>:<sequence ID><config speedup>..<config speedup><bottleneck resource>_<bottleneck type>
def main(arg):
    if (len(arg)) == 1:
        print "Usage: {0} input\n".format(arg[0])
        exit()
    
    
    f = open( arg[1] + "/critPath.bin", "wb")
    
    taskCount = 0
    array('h', [len(arg) - 1]).tofile(f)
    array('c', '-').tofile(f)
    taskCountPos = f.tell()
    array('i', [taskCount]).tofile(f)
    
    # loop through each context file and add it to the master output
    #   Will need to simultaneously read from every file in the input directories
    for ctFile in os.listdir(arg[1]):
        # Skip any files with suffixes
        if (len(ctFile.split(".")) > 1):
            continue

        ctFileIn = open(arg[1] + "/" + ctFile, "r")
        
        # for each line, first is the context:sequence ID pair
        #   then header
        #   then 12 lines of bottlenecks
        #   skip 3
        #   then performance
        state = 0
        for l in ctFileIn:
            
            if (state == 0):
                m = re.match("\d+:\d+", l)
                if (m):
                    context, sequence = l.split(":")
                    array('i', [int(context)]).tofile(f)
                    array('c', ':').tofile(f)
                    array('i', [int(sequence)]).tofile(f)
                    state = 1
                    taskCount += 1
                    continue
            if (state == 1):
                m = re.match("INT_ADDER", l)
                if (m):
                    state = 2
                    line = 0
                    minline = 0
                    minvalue = -1.0
                    mintype = 0
                else:
                    continue
            if (state == 2):
                bvals = l.split() #no arg splits on whitespace
                issue = float(bvals[1])
                latency = float(bvals[2])
                if (minvalue == -1):
                    minvalue = issue
                    minline = line
                    mintype = 0
                if (issue < minvalue):
                    minvalue = issue
                    minline = line
                    mintype = 0
                if (latency < minvalue):
                    minvalue = issue
                    minline = line
                    mintype = 1
                line += 1
                if (line == 13):
                    state = 3
                continue
            if (state == 3):
                m = re.match("PERFORMANCE\s+[0-9.]+", l)
                if (m):
                    state = 0
                    # perf will be used to compare between configs to compute speedup
                    #   versus the first config (i.e. baseline)
                    perf = float(l.split()[1])
                    array('f', [1.0]).tofile(f)
                    array('h', [minline]).tofile(f)
                    array('c', '_').tofile(f)
                    array('h', [mintype]).tofile(f)
                    
    
    f.seek(taskCountPos, 0)
    array('i', [taskCount]).tofile(f)
    f.close()

if __name__ == "__main__":
    main(sys.argv)