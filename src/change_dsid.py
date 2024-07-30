#!/usr/bin/env python


import sys
import os
import re
import pdb



def main(filename, outfile):
    ofile = open(outfile, 'w')
    with open(filename) as fh:
        for l in fh:
            regex = r'ds([0-9][0-9][0-9])\.([0-9])'
            regex_replacement = r'd\g<1>00\2'
            str_output = re.sub(regex, regex_replacement, l)
            ofile.write(str_output)
            #print(l)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f'Convert dsxxx.x to dxxx.xxx')
        print(f'usage: {sys.argv[0]} [filename] [outfile]')
        exit(1)
    main(sys.argv[1], sys.argv[2])
