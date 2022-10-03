#!/bin/bash
ping_result=$(fping -p 1 -c 10 $1 2>&1| tail -n 1)
ping_loss=$(echo ${ping_result}| awk '{print $5}' | awk -F '/' '{print $3}'| awk -F '%' '{print int($1)}')
ping_sec=$(echo ${ping_result}| awk '{print $NF}' | cut -d '/' -f2)
ipinfo=$(curl -s ifconfig.me)
echo $ping_loss,$ping_sec,$ipinfo
