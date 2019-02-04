#!/bin/bash

### Log ###
logsDir=/data/logs/tomcat
log="$logsDir/numconnect"
numOpenFiles=`/usr/sbin/lsof -u tomcat | wc | awk '{print $1}'`
echo "`date` -- $numOpenFiles" >> $log 2>&1

###################
### Error Check ###
###################

mailRecipients='rpconroy@ucar.edu'

# Check open files
openFileLimit=2500
if [[ $numOpenFiles -gt $openFileLimit ]]; then
    errorMsg="Too many open files for tomcat. Nearing max.\nNumber of open files :$numOpenFiles"
    subject="Warning: Tomcat too many open files"
    echo "$errorMsg" | mail -s "$subject" $mailRecipients
fi

#Check internal server errors
logDate=`date +%Y-%m-%d`
linesInLastHour=300 # Estimate
ISE=`tail -$linesInLastHour /data/logs/tomcat/localhost_access_log.${logDate}.txt | grep "500 "`
if [[ $? -eq 0 ]]; then

    errorMsg="Internal server error in last hour:\n\n$ISE"
    subject="Thredds internal server error in last hour"
    echo "$errorMsg" | mail -s "$subject" $mailRecipients
fi


# Roll log
limit=100
tail -$limit $log > /tmp/tdsmonitor.tmp
mv /tmp/tdsmonitor.tmp $log


