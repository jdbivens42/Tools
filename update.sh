#!/bin/bash

lists="*.list"

while read -r f; do
    echo Building report for: $f;
    n=$(basename $f);
    out=summary-${n%.*}.html
    ./html_gen.py $f $out $(date +"%T") 


    ./unique-append.sh index.html "<div><a href=\"$out\">Report: ${n%.*}</a></div>"
done < <( find -maxdepth 1 -type f -name "$lists" )

