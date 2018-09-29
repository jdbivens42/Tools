#!/usr/bin/perl
use warnings; use strict;
use WWW::Mechanize;
use WWW::Mechanize::Plugin::FollowMetaRedirect;
use HTTP::Cookies;
use Data::Dumper;

my $cookies = {};
if ( $ARGV[1] ) {
	$cookies=HTTP::Cookies->new( ignore_discard => 1 );
	$cookies->set_cookie(undef, 'PHPSESSID', '754d60e12845cb04cf3086f54517c3c2', '/', '192.168.31.130', undef, 0, 1);
}
print Dumper($cookies);
my $mech = WWW::Mechanize->new( cookie_jar => $cookies );
$cookies->scan(sub{ print Dumper \@_ } );
my $res = $mech->get($ARGV[0]);
#printf "%s\n\n%s", $res->code, $mech->content;
my $MAX_META_REDIRECT=2;
my $i=0;
while (my $meta_redirect = $mech->follow_meta_redirect( ignore_wait => 1 )) {
	$res = $meta_redirect;
	last if ++$i >= $MAX_META_REDIRECT;
}
my @forms = $mech->forms;
printf "\n\nURI: %s\n", $mech->uri;

for my $form (@forms) {
	my $request = $form->click;
	printf "%s\t%s\n", $request->uri, $request->content;
}
