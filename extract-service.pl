#!/usr/bin/perl

#Input to ini:
# out_file_name	regex

#Input to pl:
#xml_file	regex

#Output from pl:
# service_name	address	port

use strict;
use warnings;

use XML::Simple;
use Data::Dumper;


my $ref = XMLin($ARGV[0]);

if (ref($ref->{'host'}) ne "ARRAY") {
	$ref->{'host'} = [ $ref->{'host'} ];
}



foreach my $host (@{$ref->{'host'}}) {
	
	my $addr_ref = $host->{address};
	my $ip;
	if (ref($addr_ref) eq "ARRAY"){
		$ip = $host->{address}->[0]->{addr};
	} else {
		$ip = $host->{address}->{addr};
	}
	
	if (defined $host->{ports}) {
		my @res = ();
		my $r = %{$host->{ports}}{port};
		
		if (ref($r) ne "ARRAY") {
			$r = [ $r ];
		} 
		foreach my $p (@$r) {
			if (exists $p->{service} and exists $p->{service}->{name}) {
				if ($p->{service}->{name} =~ /($ARGV[1])/  ) {
					my @keys = (qw(name product version tunnel));
					my @info =();
					push @info, $p->{service}->{$_} for (@keys);
					push @res, join( "\t", $1, $ip, $p->{portid}, join( "\t", grep defined, @info ) );
				}

			}
		}

		print @res ? join("\n", @res)."\n" : "";
	}

}
