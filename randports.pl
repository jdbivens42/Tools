#!/usr/bin/perl
use warnings; use strict;

my $DELIM=",";
my $MAX= $ARGV[1] // 65535;

my @ports;
for (my $i=0; $i<$ARGV[0]; $i++){
	push @ports, int(rand($MAX));
}
printf "%s\n", join(",", @ports);
