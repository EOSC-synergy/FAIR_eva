#!/bin/bash
kill $(lsof -t -i:5000)
kill $(lsof -t -i:9090)
/FAIR_eva/web.py &
/FAIR_eva/fair.py &
wait -n
exit $?
