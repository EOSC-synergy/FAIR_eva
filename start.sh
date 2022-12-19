#!/bin/bash

CONFIG_FILE=config.ini
if [ $# -gt 0 ] && [ -f "$1" ]; then
    CONFIG_FILE=$1
else
    echo "<$CONFIG_FILE> does not exist, using default path (config.ini)"
fi

kill $(lsof -t -i:5000)
kill $(lsof -t -i:9090)
/fair_eva/web.py -c $CONFIG_FILE &
/fair_eva/fair.py &
wait -n
exit $?
