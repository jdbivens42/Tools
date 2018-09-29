#!/usr/bin/perl
use warnings; use strict;
print `cutycapt --insecure --url=$ARGV[0] --out=$ARGV[1] --out-format=png`;
exit $?;
