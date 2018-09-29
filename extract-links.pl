#!/usr/bin/perl
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
		my @links = ();
		my $r = %{$host->{ports}}{port};
		
		if (ref($r) ne "ARRAY") {
			$r = [ $r ];
		} 
		foreach my $p (@$r) {
			if (exists $p->{service} and exists $p->{service}->{name}) {
				if ($p->{service}->{name} =~ /http/  ) {
					my $proto = "http";
					my $tunnel = $p->{service}->{tunnel};
					if ($tunnel && $tunnel =~ /ssl/){
						$proto.="s";
					}
					push @links, "$proto://$ip:$p->{portid}/";
				}

			}
		}

		print @links ? join("\n", @links)."\n" : "";
	}

}
