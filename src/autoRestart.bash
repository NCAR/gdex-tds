#!/bin/bash

cd /glade/u/home/rpconroy/repositories/rda-tds/
git pull -q

curl --fail https://tds.gdex.ucar.edu/thredds --connect-timeout 6 https://tds.gdex.ucar.edu/thredds
if [[ $? -ne 0 ]]; then
    echo "Restart on `date`"
    echo "Restart on `date`" >> /glade/u/home/rpconroy/repositories/rda-tds/rda-tds/README.md
    git add -u
    git commit -m "Pod restart"
    git push origin
else 
    echo "OK      on `date`"
fi

