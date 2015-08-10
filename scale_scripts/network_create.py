#! /usr/bin/python

# Modified version of dh.py for network scaling
# Usage   : ./port_create.py <Number of DHCP networks> <Number of DHCP ports per network> [-delete]
# Example : ./port_create.py 3 10
# Example : ./port_create.py 10 20
# Example : ./port_create.py -delete

import os
import sys
from multiprocessing import Pool
import time
from datetime import datetime
from neutronclient.v2_0 import client as neutron_client

dhcp_networks = 0
dhcp_ports_per_network = 0

if len(sys.argv) == 2 and sys.argv[1] == "-delete":
    pass
elif  len(sys.argv) == 3:
    if sys.argv[1].isdigit():
        dhcp_networks = int(sys.argv[1])
    else:
        print "\n Wrong usage\n"
        sys.exit(0)
    if sys.argv[2].isdigit():
        dhcp_ports_per_network = int(sys.argv[2])
    else:
        print "\n Wrong usage\n"
        sys.exit(0)
else:
    print "\n Wrong usage\n"
    sys.exit(0)

def get_neutron_credentials():
    d = {}
    d['username'] = os.environ['OS_USERNAME']
    d['password'] = os.environ['OS_PASSWORD']
    d['auth_url'] = os.environ['OS_AUTH_URL']
    d['tenant_name'] = os.environ['OS_TENANT_NAME']
    return d

neutron_credentials = get_neutron_credentials()
neutron = neutron_client.Client(**neutron_credentials)

while True:
    try:
        f = os.popen("neutron net-list | grep DHCP | wc -l 2> /dev/null")
        output = f.read()
        output = output.splitlines()
        if output == []:
            time.sleep(5)
            continue
        network_subnet_start_index = int(output[0])
        break
    except:
        time.sleep(5)
        continue

# Find number of existing DHCP ports
while True:
    try:
        f = os.popen("neutron port-list | grep DHCP | wc -l")
        output = f.read()
        output = output.splitlines()
        if output == []:
            time.sleep(5)
            continue
        existing_dhcp_port_count = output[0]
        break
    except:
        time.sleep(5)
        continue

expected_dhcp_port_count = ( int(dhcp_networks) * int(dhcp_ports_per_network) ) + int(existing_dhcp_port_count)

mac_base_part = "fa:16:"

def get_next_mac_remaining_part(i):
    m = "{:08X}".format(int("1", 16) + i)
    mac_remaining_part =':'.join(a+b for a,b in zip(m[::2], m[1::2]))
    return mac_remaining_part

def t_create_network_subnet_ports(i, p):
    neutron_credentials = get_neutron_credentials()
    neutron = neutron_client.Client(**neutron_credentials)

    # Create DHCP network
    network_name = "DHCP-network-" + str(i)
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
    global dhcp_networks
    if dhcp_networks == 1:
        cidr = "1.0.0.0/16"
    else:
        cidr = "1.0.0.0/24"

    gateway_ip = "1.0.0.1"
    subnet_name = "DHCP-subnet-" + str(i)
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

    # Create DHCP ports
    mac_index = -1
    global mac_base_part
    for j in range(0, p):
        port_name = "DHCP-port-" + str(i) + "-" + str(j)
        port_mac_address = mac_base_part + get_next_mac_remaining_part(mac_index)
        mac_index = mac_index + 1
        json = {'port': {
            'admin_state_up': True,
            'name': port_name,
            'mac_address': port_mac_address,
            'network_id': network_id}}
        while True:
            try:
                port = neutron.create_port(body=json)
                break
            except:
                continue

def t_delete_ports_subnet_network(network):
    neutron_credentials = get_neutron_credentials()
    neutron = neutron_client.Client(**neutron_credentials)

    # Delete ports
    ports = neutron.list_ports(network_id=network['id'])['ports']
    for port in ports:
        while True:
            try:
                neutron.delete_port(port['id'])
                break
            except:
                continue

    # Delete subnet
    while True:
        try:
            if network['subnets'] == []:
                break
            else:
                neutron.delete_subnet(network['subnets'][0])
                break
        except:
            continue

    # Delete network
    while True:
        try:
            ns = "qdhcp-" + str(network['id'])
            neutron.delete_network(network['id'])
            os.system("sudo ip netns delete " + ns + " &> /dev/null")
            break
        except:
            os.system("sudo ip netns delete " + ns + " &> /dev/null")
            continue

pool = Pool(processes=100)

# Delete DHCP test ports, test subnets, test networks
if len(sys.argv) == 2 and sys.argv[1] == "-delete":
    # Delete neutron logs
    os.system("rm -rf /var/log/neutron/*.gz")
    os.system("rm -rf /var/log/neutron/*metadata*.log")
    # os.system("> /var/log/neutron/dhcp-agent.log")
    os.system("> /var/log/neutron/server.log")
    os.system("> /var/log/neutron/openvswitch-agent.log")
    os.system("> /var/log/neutron/dnsmasq.log")
    os.system("> /var/log/neutron/dhcp-relay.log")
    os.system("> /var/log/neutron/dns-relay.log")
 
    os.system("./device_manager.py -delete > /dev/null")

    # Delete all DHCP networks, subnets and ports

    while True:
        try:
            networks = neutron.list_networks()['networks']
            break
        except:
            continue

    for network in networks:
        if "DHCP" in network['name']:
            pool.apply_async(t_delete_ports_subnet_network, (network, ))

    # print "\nWaiting for DHCP networks to be deleted....\n"

    while True:
        try:
            f = os.popen("neutron net-list | grep DHCP | wc -l")
            output = f.read()
            output = output.splitlines()
            if output == []:
                time.sleep(5)
                continue
            if output[0] == str(0):
                break
            else:
                print "{0} : {1} networks remaining".format(str(datetime.now()), output[0])
                time.sleep(5)
        except:
            continue

    os.system("./device_manager.py -delete > /dev/null")
 
    # print "\nDone!\n"

    sys.exit(0)

# Delete old neutron logs
os.system("rm -rf /var/log/neutron/*.gz")
os.system("rm -rf /var/log/neutron/*metadata*.log")
os.system("> /var/log/neutron/dhcp-agent.log")
os.system("> /var/log/neutron/server.log")
os.system("> /var/log/neutron/openvswitch-agent.log")
os.system("> /var/log/neutron/dnsmasq.log")
os.system("> /var/log/neutron/dhcp-relay.log")
os.system("> /var/log/neutron/dns-relay.log")

# Increase Neutron quota for network, subnet and port
tenant_id = neutron.get_quotas_tenant()['tenant']['tenant_id']
json = {'quota': {'network': 100000, 'subnet': 100000, 'port': 100000}}
neutron.update_quota(tenant_id, body=json)

print "\nWaiting for DHCP network, subnet and ports to be created...."
 
for n in range(0, dhcp_networks):
    pool.apply_async(t_create_network_subnet_ports, (network_subnet_start_index, dhcp_ports_per_network))
    network_subnet_start_index = network_subnet_start_index + 1

if "-delete" not in sys.argv:
    while True:
        try:
            f = os.popen("neutron port-list | grep DHCP | wc -l")
            output = f.read()
            output = output.splitlines()
            if output == []:
                time.sleep(5)
                continue
            if output[0] != "0":
                print "{0} : {1} ports found. {2} ports expected".format(str(datetime.now()), output[0], expected_dhcp_port_count)
            if output[0] == str(expected_dhcp_port_count):
                # print "\nDone!\n"
                break
            else:
                time.sleep(5)
        except:
            continue
