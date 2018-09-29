#!/usr/bin/perl
#Usage: purge-report.pl path-to-report

use warnings; use strict;
use Cwd;
use File::Path;
use File::Spec;

my $dir = cwd;
my $report;
if ( !$ARGV[0] ) {
	print "Warning! This will delete ALL reports! Do you want to continue? [y/N]";
	my $response=<>;
	chomp($response);
	if ($response !~ /^y|Y/){		
		exit 0;
	}
}
else {
	$report = $ARGV[0];
}
opendir(my $dh, $dir) || die("Can't open $dir: $!");

while(readdir $dh) {
	if (-d && /(\d+\.?){4}/) {
		my $path = File::Spec->catfile($dir, $_);
		if ($report) {
			$path = File::Spec->catfile($path, $report);
		}

		printf "Purging: %s\n", $path;

		if (-d $path){
			rmtree($path);
		} else {
			unlink($path);
		}
	}
}
closedir $dh
