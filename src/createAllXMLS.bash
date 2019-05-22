#!/bin/bash


for i in `cat thredds_dsids`; do 
    ./createXML.py $i > catalog_${i}.xml
done
