#!/bin/bash

if [ $# != 2 ]; then
    echo -e "\n\n  Number of arguments is wrong\n\n"
    exit 1
fi

interface_count=$1
interface_status=$2

interface_up_down_errors='interface_'${interface_status}_'errors'

rm -rf dhclient.log
rm -rf interface_up_errors
rm -rf interface_down_errors
rm -rf ip_addr_flush_errors

if [ $interface_status == "down" ]; then
    # Forget remembered old leases and DHCP server
    sudo rm -rf /var/lib/dhcp/dhclient.leases
fi

for (( i=1; i<=$interface_count; i++ ))
do
    sudo ifconfig eth${i} $interface_status 2>> $interface_up_down_errors

    if [ $interface_status == "down" ]; then
        sudo ip addr flush dev eth${i} 2>> ip_addr_flush_errors
    else
        sudo dhclient -v eth${i} &>> dhclient.log
    fi
done

# Delete the file $interface_up_down_errors if it is empty
if [ -s $interface_up_down_errors ]
then
    echo ""
else
    rm -rf $interface_up_down_errors
fi

# Delete the file ip_addr_flush_errors if it is empty
if [ -s ip_addr_flush_errors ]
then
    echo ""
else
    rm -rf ip_addr_flush_errors
fi
