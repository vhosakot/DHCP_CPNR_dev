#! /usr/bin/python

import os
import thread
import time
import sys
from neutronclient.v2_0 import client as neutron_client

def get_neutron_credentials():
    d = {}
    d['username'] = os.environ['OS_USERNAME']
    d['password'] = os.environ['OS_PASSWORD']
    d['auth_url'] = os.environ['OS_AUTH_URL']
    d['tenant_name'] = os.environ['OS_TENANT_NAME']
    return d

neutron_credentials = get_neutron_credentials()
neutron = neutron_client.Client(**neutron_credentials)

if len(sys.argv) == 2 and sys.argv[1] == "-delete":
    f = os.popen("neutron port-list | grep 'existing\|new' | awk \'{print $2}\' 2> /dev/null")
    output = f.read()
    output = output.splitlines()
    for i in output:
        try:
            neutron.delete_port(i)
        except:
            pass
    
    f = os.popen("neutron subnet-list | grep new | awk \'{print $2}\' 2> /dev/null")
    output = f.read()
    output = output.splitlines()
    for i in output:
        try:
            neutron.delete_subnet(i)
        except:
            pass
    
    f = os.popen("neutron net-list | grep new | awk \'{print $2}\' 2> /dev/null")
    output = f.read()
    output = output.splitlines()
    for i in output:
        try:
            neutron.delete_network(i)
        except:
            pass

    sys.exit(0)

def t_create_port(json):
    neutron_credentials = get_neutron_credentials()
    neutron = neutron_client.Client(**neutron_credentials)

    while True:
        try:
            port = neutron.create_port(body=json)
            break
        except:
            continue

def t_delete_port(port_id):
    neutron_credentials = get_neutron_credentials()
    neutron = neutron_client.Client(**neutron_credentials)

    while True:
        try:
            neutron.delete_port(port_id)
            break
        except:
            continue

def t_create_network_subnet_port(n, new_ports_new_network):
    neutron_credentials = get_neutron_credentials()
    neutron = neutron_client.Client(**neutron_credentials)

    # Create DHCP network
    network_name = "new-network-" + str(n)
    json = {'network': {'name': network_name, 'admin_state_up': True}}
    while True:
        try:
            netw = neutron.create_network(body=json)
            break
        except:
            continue
    net_dict = netw['network']
    network_id = net_dict['id']

    # Create DHCP subnet
    cidr = "252." + str(n % 254) + ".0.0/16"
    gateway_ip = "252." + str(n % 254) + ".0.1"
    subnet_name = "new-subnet-" + str(n)
    json = {'subnets': [{'cidr': cidr,
                     'ip_version': 4,
                     'network_id': network_id,
                     'gateway_ip': gateway_ip,
                     'name': subnet_name}]}
    while True:
        try:
            subnet = neutron.create_subnet(body=json)
            break
        except:
            continue

    # Create DHCP ports in each new network
    for j in range(0, new_ports_new_network):
        json = {'port': {
            'admin_state_up': True,
            'name': "port-in-new-network-" + str(n) + "-" + str(j),
            'network_id': network_id}}
        thread.start_new_thread(t_create_port, (json,))

networks_to_churn = 2
dhcp_ports_per_network_to_churn = 3
delay_during_churn = 1

################
f = os.popen("neutron net-list | grep DHCP | wc -l 2> /dev/null")
output = f.read()
output = output.splitlines()
dhcp_network_count = int(output[0])

script_ended = False
################

def churn_ports_in_existing_dhcp_networks():
    global script_ended
    global dhcp_network_count
    global dhcp_ports_per_network_to_churn
    network_ids = []
    n = 0

    for i in range(0, dhcp_network_count):
        network_name = "DHCP-network-" + str(i)
        while True:
            try:
                network_ids.append(neutron.list_networks(name=network_name)['networks'][0]['id'])
                break
            except:
                continue
 
    while script_ended is False:
        # Create ports in each existing DHCP network
        for network_id in network_ids:
            for j in range(0, dhcp_ports_per_network_to_churn):
                json = {'port': {
                    'admin_state_up': True,
                    'name': "port-in-existing-network-" + str(n),
                    'network_id': network_id}}
                thread.start_new_thread(t_create_port, (json,))
                n = n + 1
        
        # Sleep for few seconds after creating ports
        time.sleep(delay_during_churn)

        # Delete ports in each existing DHCP network
        f = os.popen("neutron port-list | grep port-in-existing-network- | awk \'{print $2}\' 2> /dev/null")
        output = f.read()
        output = output.splitlines()
        for port_id in output:
            thread.start_new_thread(t_delete_port, (port_id,))

        # Sleep for 5 seconds after deleting ports
        time.sleep(1)

def churn_ports_in_new_dhcp_networks():
    global script_ended
    global networks_to_churn
    global dhcp_ports_per_network_to_churn
    n = 0

    while script_ended is False:
        # Create new DHCP networks, subnets and ports
        for i in range(0, networks_to_churn):
            thread.start_new_thread(t_create_network_subnet_port, (n, dhcp_ports_per_network_to_churn))
            n = n + 1

        # Sleep for few seconds after creating networks, subnets and ports
        time.sleep(delay_during_churn)

        # Delete ports in each new DHCP network
        f = os.popen("neutron port-list | grep port-in-new-network- | awk \'{print $2}\' 2> /dev/null")
        output = f.read()
        output = output.splitlines()
        for port_id in output:
            thread.start_new_thread(t_delete_port, (port_id,))

        # Sleep for 5 seconds after deleting ports
        time.sleep(1)

        # Delete new DHCP subnets
        f = os.popen("neutron subnet-list | grep new-subnet- | awk \'{print $2}\' 2> /dev/null")
        output = f.read()
        output = output.splitlines()
        for subnet_id in output:
            try:
                neutron.delete_subnet(subnet_id)
            except:
                pass

        # Delete new DHCP networks
        f = os.popen("neutron net-list | grep new-network- | awk \'{print $2}\' 2> /dev/null")
        output = f.read()
        output = output.splitlines()
        for network_id in output:
            ns = "qdhcp-" + network_id
            try:
                neutron.delete_network(network_id)
                os.system("sudo ip netns delete " + ns + " &> /dev/null")
            except:
                os.system("sudo ip netns delete " + ns + " &> /dev/null")
                pass

        # Sleep for 5 seconds after deleting subnets and networks
        time.sleep(1)

thread.start_new_thread(churn_ports_in_existing_dhcp_networks, ())
thread.start_new_thread(churn_ports_in_new_dhcp_networks, ())

while True:
    pass
