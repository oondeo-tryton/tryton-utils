#!/bin/bash

if [ -z "$1" ]; then 
    echo "The db name is missing"
    exit 1
fi

if [ -z "$2" ]; then 
    echo "The new owner name is missing"
    exit 1
fi

if [ -z "$3" ]; then 
    port=5432
else
    port=$3
fi

psql -p $port $1 -c "alter database \"$1\" owner to $2;"

command="pg_dump -p $port -s $1 | grep -i 'owner to' | sed -e 's/OWNER TO .*;/OWNER TO $2;/i' | psql -p $port $1"
eval $command

exit 0
