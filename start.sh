#!/bin/bash

# Start the first process
./web.py &
  
# Start the second process
./fair.py &
  
# Wait for any process to exit
wait -n
  
# Exit with status of process that exited first
exit $?
