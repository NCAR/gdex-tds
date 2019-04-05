#!/usr/bin/env python
import xml.etree.ElementTree as ET
import mysql.connector as sql
from HTMLParser import HTMLParser
import pdb
import sys


def usage():
    sys.stderr.write('Usage:\n')
    sys.stderr.write('    ' + sys.argv[0] + ' [dsid]\n')
    exit(1)

def get_dsid():
    """get dsid arg, check if valid and fix if possible."""
    dsid = sys.argv[1]
    if len(dsid) < 5 or len(dsid) > 7:
        sys.stderr.write('dsid, "' + dsid + '" is not valid\n')
        exit(1)
    return  dsid.split('ds')[-1]

def strip_html(text):
    parts = []
    parser = HTMLParser()
    parser.handle_data = parts.append
    parser.feed(text)
    return ''.join(parts)

def get_format(formt):
    """Returns thredds format string.
    NOTE: this a simplistic method to get the string. There are
    many other format strings that would also work.
    """
    formt = formt.lower()
    if 'netcdf' in formt:
        return 'NetCDF'
    if 'grib1' in formt:
        return 'GRIB-1'
    if 'grib2' in formt:
        return 'GRIB-2'
    sys.stderr.write('Format:' +formt+ ' doesn\'t have a mapping')
    exit(1)

def check_same(arr):
    """Checks if all values are the same in an array."""
    test_ele = arr.pop()
    for i in arr:
        if test_ele.__hash__() != i.__hash__():
            sys.stderr.write('Values not all the same')
            sys.stderr.write(str(i)+' != '+str(test_ele))
            exit(1)




if len(sys.argv) > 2 or len(sys.argv) == 1:
    usage()

dsid = get_dsid()

dsid = '084.1'
conn = sql.connect(user = 'metadata', password='metadata', host = 'rda-db.ucar.edu', database='search')
cursor = conn.cursor()

# Get title
query = 'select title from datasets where dsid=' + dsid
cursor.execute(query)
title, = cursor.fetchall()[0]

# Get summary
query = 'select summary from datasets where dsid='+dsid
cursor.execute(query)
summary, = cursor.fetchall()[0]
summary = strip_html(summary)

# Get format
query = 'select keyword from formats where dsid='+dsid
cursor.execute(query)
formt, = cursor.fetchall()[0]
formt = get_format(formt)
cursor.reset()

# Get Datatype
query = 'select keyword from data_types where dsid='+dsid
cursor.execute(query)
datatypes = cursor.fetchall()
check_same(datatypes)
datatype, = datatypes[0]

root = ET.Element('catalog')
title = 'select title from datasets where dsid='+dsid
root.attrib['name'] = title
root.attrib['xmlns'] = 'http://www/unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0'
root.attrib['xmlns:xlink'] = 'http://www/w3.org/1999/xlink'

comment = 'Top level dataset: Needed to set metadata for Files & Aggregations -->'
root.append(ET.Comment(comment))

dataset = ET.SubElement(root, 'dataset')
dataset.attrib['name'] =  title


metadata = ET.SubElement(dataset, 'metadata')
metadata.attrib['inherited'] = 'true'

service_name = ET.SubElement(metadata, 'serviceName')
service_name.text = 'Freely Available'

data_format = ET.SubElement(metadata, 'dataFormat')
data_format.text = formt





print(ET.tostring(root))
