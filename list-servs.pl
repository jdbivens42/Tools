#!/usr/bin/perl
use warnings; use strict;
use File::Spec;

my $pattern=$ARGV[0];
my $service_report=$ARGV[1] // File::Spec->catfile('Services', '.tcp-services');
my $host_file=$ARGV[2] // 'hosts.list';

my @cmd = ('./extract-service.pl', undef, $pattern);

open FH, $host_file;
while(<FH>) {
	chomp;
	$cmd[1] = File::Spec->catfile($_, $service_report);
	print qx{@cmd};
}
close FH;

