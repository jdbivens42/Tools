#!/usr/bin/perl
use warnings; use strict;
my $url = $ARGV[0];
my $img = $ARGV[1];

my $html_link = sprintf "<div><a href='%s' target='_blank'>%s</a></div>", $url, $url;
my $html_img;

if ($img) {
	$html_img = sprintf "<div style='height:20em;overflow:auto;'><img src='%s'/></div>", $img;
}

printf "%s", $html_link;
printf "%s", $html_img if $html_img;
print "\n";
