#!/usr/bin/env python
from siphon.catalog import TDSCatalog
import numpy as np
import  xml.etree.ElementTree as ET
import requests
import pdb
import sys
import yaml


def get_value(in_dict, key):
    """Gets the value of key while ignoring namepaces
    """
    for k in in_dict.keys():
        split_key = k.split('}')[-1]
        if key == split_key:
            return in_dict[k]
    return None

def check_services(xmlEles):
    """Asserts that all services in the Eles are expected
    as defined in expectedServices.yaml
    """
    print("Checking correct services")
    expectedServices = yaml.load(open('expectedServices.yaml','r'))
    services = [i.attrib['serviceType'] for i in xmlEles]

    for expectedService in expectedServices:
        assert expectedService in services
    print("Good")

def check_catalog(catalog_url):
    """Checks catalog to see if things are working
    """
    print("Checking ", catalog_url)
    rq = requests.get(catURL)
    xml_str = rq.content
    root = ET.fromstring(xml_str)
    print("Good")

domain = "https://rda.ucar.edu/"
if len(sys.argv) > 1:
    if sys.argv[1] == 'DEV':
        domain = "https://rda-web-dev.ucar.edu/"

thredds_root = "thredds/catalog/"
catURL = domain + thredds_root + "catalog.xml"
datasetName = "fnl_20010306_18_00.grib1"

print("downloading root catalog: " + catURL)
rq = requests.get(catURL)
xml_str = rq.content
root = ET.fromstring(xml_str)
namespace = root.tag.split('}')[0]+'}'
print("Iterating through catalog")

# Find services defined in the catalog
serviceEle = root.findall(namespace+'service')
print("Checking there's only one service element")
assert len(serviceEle) == 1
print("Good")
serviceEles = serviceEle[0].findall(namespace+'service')
check_services(serviceEles)

for cat in root.findall(namespace+'catalogRef'):
    catalog = get_value(cat.attrib, 'href')
    catalog_url = domain + thredds_root + catalog
    check_catalog(catalog_url)


