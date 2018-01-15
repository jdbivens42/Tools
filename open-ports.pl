#!/usr/bin/perl
use strict;
use warnings;

use XML::Simple;

my $ref = XMLin($ARGV[0]);

foreach my $host (@{$ref->{'host'}}) {
	
	# remove [0] if MAC addresses were not returned
	my $addr_ref = $host->{address};
	my $ip;
	if (ref($addr_ref) eq "ARRAY"){
		$ip = $host->{address}->[0]->{addr};
	} else {
		$ip = $host->{address}->{addr};
	}
	
	if (defined $host->{ports}) {
		my @ports = ();
		my $r = %{$host->{ports}}{port};
		
		if (ref($r) eq "ARRAY") {
			foreach my $p (@$r) {
				push @ports, $p->{portid};
			}
		} else {
			push @ports, $r->{portid};
		}
		printf "%s\t%s\n", $ip, join(',', @ports);
	}

}
