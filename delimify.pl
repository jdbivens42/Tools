#!/usr/bin/perl
use warnings;
use strict;
my $delim = $ARGV[0];
printf "%s\n", join($delim, @ARGV[1..$#ARGV])
