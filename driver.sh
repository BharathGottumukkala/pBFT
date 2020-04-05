#!/bin/bash

# python3.6 Node.py &
# python3.6 Node.py

# (echo python3.6 Node.py; echo python3.6 Node.py) | parallel

# NEVER MIND THIS FILE

control_c() {
    kill $(ps aux | grep Node.py | awk '{print $2}')
    exit
}

trap control_c SIGINT


read -p "Enter number of nodes : " N

# N=4
python3.6 Node.py --primary &
echo $!
sleep 1

for i in $(seq 2 $N);
do
	python3.6 Node.py &
	echo $!
	sleep 1
done

wait


# python3.6 Node.py &
# P1=$!
# sleep 1
# python3.6 Node.py &
# P2=$!
# wait $P1 $P2