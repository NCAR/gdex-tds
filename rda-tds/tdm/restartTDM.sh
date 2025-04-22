#!/bin/bash

pid=`ps -ef | grep tdm | grep -v grep | awk -F' ' '{print $2}' | head`
if [[ ! -z $pid ]]; then
	kill $pid
	echo "killed $pid"
fi
./runTdm.sh >tdm.log 2>&1 &

