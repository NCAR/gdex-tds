#!/bin/bash


for i in catalog_*.xml
    {
        grep -i 'You must change this' $i
        #if [[ $? -eq 0 ]]; then # It needs changing
            echo $i
            name=`grep "dataset name" $i | grep -o '\".*\"'`
            echo name
            sed -i "s/<catalog name=.*/<catalog name=$name/" $i
        #fi
    }
