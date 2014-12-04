#!/bin/bash

if [ $# != 2 ]; then
    echo -e "\n\n  Number of arguments is wrong\n\n"
    exit 1
fi

interface_count=$1
interface_status=$2

if [ $interface_status == "down" ]; then
    # Forget remembered old leases and DHCP server
    sudo rm -rf /var/lib/dhcp/dhclient.leases
fi

if [ $interface_status == "dhclient" ]; then
    rm -rf *_dhclient.log
    rm -rf dhclient.log
fi

if [ $interface_status == "generate_dhclient_log" ]; then
    rm -rf dhclient.log
    for (( i=1; i<=$interface_count; i++ ))
    do
        cat eth${i}_dhclient.log &>> dhclient.log
        echo -e "\n------------------------\n" >> dhclient.log
    done
    rm -rf *_dhclient.log
    echo -e "\ndhclient.log is at /home/ubuntu/dhclient.log in the VM dhcp-scale-VM\n"
    exit 1
fi

start_time=`date +%s`
wait_time=300

for (( i=1; i<=$interface_count; i++ ))
do
    if [ $interface_status == "down" ]; then
        sudo ifconfig eth${i} down
        sudo ip addr flush dev eth${i}
    elif [ $interface_status == "up" ]; then
        sudo ifconfig eth${i} up
    elif [ $interface_status == "dhclient" ]; then
        sudo dhclient -v eth${i} &> eth${i}_dhclient.log &
    fi
done

if [ $interface_status == "dhclient" ]; then
    echo -e "\nRunning dhclient on all interfaces. Please wait...\n"
    while true; do
        if [[ -n $(ps -Ae -o ppid,command | grep $$ | grep dhclient | grep -v 'grep\|interface_bounce.sh') ]]; then
            end_time=`date +%s`
            time_waited=`expr $end_time - $start_time`
            if [ "$time_waited" -gt "$wait_time" ]; then
                sudo pkill -f dhclient
                pkill -P $$
                break
            fi
            sleep 0.5
        else
            break
        fi
    done
fi

sudo pkill -f dhclient
