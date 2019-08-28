#!/usr/bin/env python
import xml.etree.ElementTree as ET
import mysql.connector as sql
from HTMLParser import HTMLParser
import pdb
import sys


def usage():
    sys.stderr.write('Usage:\n')
    sys.stderr.write('    ' + sys.argv[0] + ' [dsid] \n')
    exit(1)

def get_dsid():
    """get dsid arg, check if valid and fix if possible."""
    if(len(sys.argv) <= 1):
        usage()
    dsid = sys.argv[1]
    if len(dsid) < 5 or len(dsid) > 7:
        sys.stderr.write('dsid, "' + dsid + '" is not valid\n')
        exit(1)
    return  dsid.split('ds')[-1]

def write_seperator():
    """Write '<:>' to stdout"""
    sys.stdout.write('<:>')

def create_ctl_entry(dsid, specialist, access_type, dirname="", gindex=None):

    if len(dirname) > 0 and dirname[-1] != '/':
        dirname += '/'
    dirname += "catalog.html"


    sys.stdout.write('0') # Write 0 because index is not yet defined
    write_seperator()
    sys.stdout.write('ds'+dsid)
    write_seperator()
    if gindex is None:
        sys.stdout.write('0') # Write 0 when refering to all products
    else:
        sys.stdout.write(str(gindex))
    write_seperator()
    sys.stdout.write('N')
    write_seperator()
    sys.stdout.write('A')
    write_seperator()
    sys.stdout.write('N')
    write_seperator()
    sys.stdout.write(specialist)
    write_seperator()
    write_seperator()
    sys.stdout.write('N')
    write_seperator()
    sys.stdout.write('https://rda.ucar.edu/thredds/catalog/files/'+access_type+'/ds'+dsid+'/'+dirname)
    write_seperator()
    write_seperator()
    sys.stdout.write('\n')

if __name__ == "__main__":

    dsid = get_dsid()


    ## New Connection to dssdb
    conn = sql.connect(user = 'metadata', password='metadata', host = 'rda-db.ucar.edu', database='dssdb')
    cursor = conn.cursor()

    # Get Specialist
    query = "select specialist from dsowner where dsid='ds"+ dsid + "';"
    cursor.execute(query)
    specialist, = cursor.fetchall()[0]

    # Get Access rights
    query = "select access_type from dataset where dsid='ds"+ dsid + "';"
    cursor.execute(query)
    rights, = cursor.fetchall()[0]
    if rights is not None:
        access_type = rights
    else:
        access_type = 'g'

    query = " select grpid,gindex from dsgroup where dsid='ds"+ dsid + "' and pindex=0;"
    cursor.execute(query)
    #grpid,gindex = cursor.fetchall()
    all_ents = cursor.fetchall()

    create_ctl_entry(dsid, specialist, access_type) # Create group 0

    for grpid,gindex in all_ents:
        create_ctl_entry(dsid, specialist, access_type, grpid, gindex)  # Create group 0

#1317<:>ds633.0<:>38<:>N<:>A<:>N<:>davestep<:><:>N<:>https://rda.ucar.edu/thredds/catalog/files/e/ds633.0/e5.oper.fc.sfc.minmax/catalog.html<:><:>

