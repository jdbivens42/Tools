#!/bin/bash
read -r ip name;
for d in General OS Services Vulns-Possible Vulns-Confirmed;
do
	mkdir -p $ip/$d/.img
done

echo $name> $ip/General/name;
echo $name | cut -d"." -f1 --complement > $ip/General/domain
echo $ip
