#!/usr/bin/env python
"""
Creates Thredds xml file for a given dataset.
"""
import xml.etree.ElementTree as ET
import mysql.connector as sql
import pdb
import sys
try:
    from HTMLParser import HTMLParser
except:
    from html.parser import HTMLParser

def usage():
    sys.stderr.write('Usage:\n')
    sys.stderr.write('    ' + sys.argv[0] + ' [dsid] [out dir]\n')
    exit(1)

def prettify(element, indent='  '):
    queue = [(0, element)]  # (level, element)
    while queue:
        level, element = queue.pop(0)
        children = [(level + 1, child) for child in list(element)]
        if children:
            element.text = '\n' + indent * (level+1)  # for child open
        if queue:
            element.tail = '\n' + indent * queue[0][0]  # for sibling open
        else:
            element.tail = '\n' + indent * (level-1)  # for parent close
        queue[0:0] = children  # prepend so children come before siblings

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
    #exit(1)
    return 'NetCDF'

def get_dsOverview_xml(dsid):
    try: # Try using filesystem
        filename = '/data/web/datasets/ds'+dsid+'/metadata/dsOverview.xml'
        tree = ET.parse(filename)
        root = tree.getroot()
    except: # Otherwise, get from web
        import requests
        url = 'https://rda.ucar.edu/datasets/ds'+dsid+'/metadata/dsOverview.xml'
        req = requests.get(url)
        xml_str = req.content
        root = ET.fromstring(xml_str)
    return root

def check_same(arr):
    """Checks if all values are the same in an array."""
    test_ele = arr.pop()
    for i in arr:
        if test_ele.__hash__() != i.__hash__():
            sys.stderr.write('Values not all the same')
            sys.stderr.write(str(i)+' != '+str(test_ele))
            exit(1)
    return True

if __name__ == '__main__':
    if len(sys.argv) > 3 or len(sys.argv) == 1:
        usage()

    dsid = get_dsid()
    output_filename = None
    if len(sys.argv) == 3:
        directory = sys.argv[2]
        output_filename = directory+'catalog_'+dsid+'.xml'


    ## New Connection to search db
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
    try:
        datatype, = datatypes[0]
    except:
        datatype = 'GRID'
    datatype = datatype.upper()

    # Get creator
    query = 'select g.path from contributors_new as c left join GCMD_providers as g on g.uuid = c.keyword where c.dsid = '+dsid+' and c.vocabulary = "GCMD"'
    cursor.execute(query)
    creators = cursor.fetchall()

    # Get keywords
    query = 'select g.path from projects_new as c left join GCMD_projects as g on g.uuid = c.keyword where c.dsid = '+dsid+' and c.vocabulary = "GCMD"'
    cursor.execute(query)
    keywords = cursor.fetchall()

    conn.close()

    ## New Connection to dssdb
    conn = sql.connect(user = 'metadata', password='metadata', host = 'rda-db.ucar.edu', database='dssdb')
    cursor = conn.cursor()

    # Get Access rights
    query = "select access_type from dataset where dsid='ds"+ dsid + "';"
    cursor.execute(query)
    rights, = cursor.fetchall()[0]
    access_type = 'g'
    if rights is not None:
        access_type = rights
        rights = 'Some Restrictions Apply'
    else:
        rights = 'Freely Available'

    ## Web derived information
    dsOverview_root = get_dsOverview_xml(dsid)

    ## Begin to build xml
    root = ET.Element('catalog')
    root.attrib['name'] = title
    root.attrib['xmlns'] = 'http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0'
    root.attrib['xmlns:xlink'] = 'http://www.w3.org/1999/xlink'

    comment = 'Top level dataset: Needed to set metadata for Files & Aggregations'
    root.append(ET.Comment(comment))

    dataset = ET.SubElement(root, 'dataset')
    dataset.attrib['name'] =  title


    metadata = ET.SubElement(dataset, 'metadata')
    metadata.attrib['inherited'] = 'true'

    service_name = ET.SubElement(metadata, 'serviceName')
    service_name.text = 'all'

    data_format = ET.SubElement(metadata, 'dataFormat')
    data_format.text = formt

    data_type = ET.SubElement(metadata, 'dataType')
    data_type.text = datatype

    doc_rights = ET.SubElement(metadata, 'documentation')
    doc_rights.attrib['type'] = 'Rights'
    doc_rights.text = rights;

    doc_href = ET.SubElement(metadata, 'documentation')
    doc_href.attrib['xlink:href'] = 'http://rda.ucar.edu/datasets/ds'+dsid+'/'
    doc_href.attrib['xlink:title'] = 'NCAR RDA - ' + title + '(ds'+dsid+')'

    doc_summary = ET.SubElement(metadata, 'documentation')
    doc_summary.attrib['type'] = 'summary'
    doc_summary.text = summary

    for related_ref in root.iterfind('relatedResource'):
        ele = ET.SubElement(metadata, 'documentation')
        ele.attrib['xlink:href'] = related_ref.attrib['url']
        ele.attrib['title'] = related_ref.text

    vocabulary = 'DIF' # All are currently GCMD
    for creator in creators:
        creator_ele = ET.SubElement(metadata, 'creator')

        creator_name = ET.SubElement(creator_ele, 'name')
        creator_name.attrib['vocabulary'] = vocabulary
        creator_name.text = creator[0].split(' ')[0]

        #TODO
        contact = ET.SubElement(creator_ele, 'contact')
        contact.attrib['url'] = 'none'

    authority = ET.SubElement(metadata, 'authority')
    authority.text = 'edu.ucar.rda'

    publisher = ET.SubElement(metadata, 'publisher')
    publisher_name = ET.SubElement(publisher, 'name')
    publisher_name.attrib['vocabulary'] = 'DIF'
    publisher_name.text = 'NCAR/RDA'
    publisher_contact = ET.SubElement(publisher, 'contact')
    publisher_contact.attrib['url'] = 'http://rda.ucar.edu/'
    publisher_contact.attrib['email'] = 'rdahelp@ucar.edu'

    # Get keywords
    for keyword in keywords:
        keyword_parts = keyword[0].split('>')
        for part in keyword_parts:
            keyword_ele = ET.SubElement(metadata, 'keyword')
            keyword_ele.text = part.strip()

    dataset.append(ET.Comment('Files'))
    datasetScan = ET.SubElement(dataset, 'datasetScan')
    datasetScan.attrib['name'] = dsid + ' Files'
    datasetScan.attrib['path'] = 'files/'+access_type+'/ds'+dsid
    datasetScan.attrib['location'] = '/data/rda/data/ds'+dsid+'/'
    scan_metadata = ET.SubElement(datasetScan, 'metadata')
    scan_metadata.attrib['inherited'] = 'true'
    service_name = ET.SubElement(scan_metadata, 'serviceName')
    service_name.text = 'all'
    scan_filter = ET.SubElement(datasetScan, 'filter')
    exclude = ET.SubElement(scan_filter, 'exclude')
    exclude.attrib['wildcard'] = '*.html'
    ET.SubElement(datasetScan, 'addDatasetSize')

    # Create Feature Collections
    #FC = ET.SubElement(dataset,'featureCollection')#ds2
    #FC.attrib['name'] = 'None'
    #FC.attrib['featureType'] = 'None'
    #FC.attrib['harvest'] = 'true'
    #FC.attrib['path'] = 'None'






    prettify(root)
    xml_str = ET.tostring(root)
    xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n'+xml_str

    if output_filename is None:
        print(xml_str)
    else:
        with open(output_filename, 'w') as fh:
            fh.write(xml_str)
