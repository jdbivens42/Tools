
while read -r host url;
do 
	filename=`echo $url | cut -d":" -f3 | tr / _`
	outpath=${PWD}/${host}/Services/.${filename}.png
        cutycapt --insecure --url=$url --out=$outpath
	preview="<img src='$outpath'>"
	echo $host "<div><a href=\"$url\" target=\"_blank\">$url</a></div><div style=\"height:20em;overflow:auto;\">$preview</div>"

done < $1
