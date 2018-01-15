#!/bin/bash
# Cat $1. If file did not exist or is empty, cat $2 instead.
# if the file $2 did not exist or was empty, cat $3 and return contents,
# if possible. $3 is optional
# useful for giving default values when config files are missing
contents=$(cat $1 2>/dev/null)
contents2=$(cat $2 2>/dev/null)
if [ -n $3 ]; then contents3=$(cat $3 2>/dev/null); fi

echo ${contents:-${contents2:-$contents3}}
