#!/usr/bin/env python
from siphon.catalog import TDSCatalog
import numpy as np
import  xml.etree.ElementTree as ET
import requests
import pdb
import sys
import yaml


def get_value(in_dict, key):
    """Gets the value of key while ignoring namepaces.
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
    rq = requests.get(catalog_url)
    xml_str = rq.content
    root = ET.fromstring(xml_str)
    find_example_catalog(root)
    print("Good")

def find_catalog_in_xml(root, tag='catalogRef'):
    for i in root.iter():
        if i.tag == namespace+tag:
            return i
    return None

def find_example_catalog(url):
    """recursive function to find some terminating catalog"""
    rq = requests.get(url)
    xml_str = rq.content
    root = ET.fromstring(xml_str)
    namespace = root.tag.split('}')[0]+'}'
    cat = find_catalog_in_xml(root)
    if cat is None:
        find_catalog_in_xml('dataset')
        return cat
    href = get_value(cat.attrib,'href')

    rq = requests.get(domain+href)
    xml_str = rq.content
    new_cat_root = ET.fromstring(xml_str)
    return find_example_catalog(new_cat_root)

    return root

def check_catalog_services(domain):

    thredds_root = "thredds/catalog/"
    catURL = domain + thredds_root + "catalog.xml"

    print("downloading root catalog: " + catURL)
    rq = requests.get(catURL)
    assert rq.status_code == 200
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

if __name__ == "__main__":
    domain = "https://rda.ucar.edu/"
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == 'dev':
            domain = "https://rda-web-dev.ucar.edu/"
        if sys.argv[1].lower() == 'test':
            domain = "https://rda-web-test.ucar.edu/"
    check_catalog_services(domain)


