#!/bin/bash
# Usage: echoer.sh <outfile> [infile]
redirect=">"
while read -r line; do
	echo echo $line$redirect $1;

	if [[ $redirect == ">" ]]; then
		redirect=">>";		
	fi
done < "${2:-/dev/stdin}"
