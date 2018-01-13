
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
	echo $host $url
done
