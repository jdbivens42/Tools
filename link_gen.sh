
for line in `cat $1`;
do
	protocol="";
        service=`echo $line | cut -d'"' -f6`;
        port=`echo $line | cut -d'"' -f4`;
        host=`echo $line | cut -d'"' -f2`;
	

        if [[ $service == *"ssl/http"* ]];
        then
                protocol="https://";
        elif [[ $service == *"http"* ]];
        then
                protocol="http://";
        else
                continue;
        fi

        url=$protocol$host:$port
	outpath=${PWD}/${host}/Services/.${port}.png
        cutycapt --insecure --url=$url --out=$outpath
	preview="<img src='$outpath'>"
	echo $host "<div><a href=\"$url\" target=\"_blank\">$url</a></div><div style=\"height:20em;overflow:auto;\">$preview</div>"

done
