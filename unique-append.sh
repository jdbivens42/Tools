#!/bin/bash

file=$1
val=$2

lk=`echo $file | sed 's/\//_/g'`
exec 200>/tmp/unique-append$lk.lk
flock -w 60 200 || (echo LOCK_TIMEOUT && exit 1)
#lock is acquired; append val to file, drop duplicates, update file, release lock when script exits
echo $val>>$file
sort -uV $file -o $file

