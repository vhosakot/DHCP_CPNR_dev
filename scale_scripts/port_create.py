#! /usr/bin/python

# Modified version of dh.py for port scaling in a single network DHCP-network-0
# Usage   : ./port_create.py <Number of DHCP ports> [-delete]
# Example : ./port_create.py 10
# Example : ./port_create.py 200
# Example : ./port_create.py -delete

import os
import sys
from multiprocessing import Pool
import time
from datetime import datetime
from neutronclient.v2_0 import client as neutron_client

if len(sys.argv) != 2:
    print "\n Wrong usage\n"
    sys.exit(0)

dhcp_ports = 0

if sys.argv[1].isdigit():
    dhcp_ports = int(sys.argv[1])
elif sys.argv[1] != "-delete":
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

first_dhcp_network = []

# Check if DHCP-network-0 already exists
while True:
    try:
        first_dhcp_network = neutron.list_networks(name="DHCP-network-0")['networks']
        break
    except:
        continue

network_id_for_dhcp_ports = ""

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

pool = Pool(processes=100)

# Delete DHCP test ports, test subnets, test networks
if len(sys.argv) == 2 and sys.argv[1] == "-delete":
    # Delete neutron logs
    os.system("rm -rf /var/log/neutron/*.gz")
    os.system("rm -rf /var/log/neutron/*metadata*.log")
    os.system("> /var/log/neutron/dhcp-agent.log")
    os.system("> /var/log/neutron/server.log")
    os.system("> /var/log/neutron/openvswitch-agent.log")
    os.system("> /var/log/neutron/dnsmasq.log")
 
    os.system("./device_manager.py -delete > /dev/null")

    # Delete all DHCP test ports
    ports = neutron.list_ports()['ports']
    for port in ports:
        if "DHCP" in port['name']:
            pool.apply_async(t_delete_port, (port['id'],))

    # print "\nWaiting for DHCP ports to be deleted....\n"

    while True:
        try:
            f = os.popen("neutron port-list | grep DHCP | wc -l")
            output = f.read()
            output = output.splitlines()
            if output[0] == str(0):
                break
            else:
                print "{0} : {1} ports remaining".format(str(datetime.now()), output[0])
                time.sleep(5)
        except:
            continue

    # Delete all DHCP test subnets
    subnets = neutron.list_subnets()['subnets']
    for subnet in subnets:
        if "DHCP" in subnet['name']:
            neutron.delete_subnet(subnet['id'])
    # print "All DHCP test subnets deleted"

    # Delete all DHCP test networks
    networks = neutron.list_networks()['networks']
    for network in networks:
        if "DHCP" in network['name']:
            ns = "qdhcp-" + str(network['id'])
            neutron.delete_network(network['id'])
            os.system("sudo ip netns delete " + ns + " &> /dev/null")
    # print "All DHCP test networks and namespaces deleted\n"

    os.system("./device_manager.py -delete > /dev/null")
 
    # print "\nDone!\n")

    sys.exit(0)

# Delete old neutron logs
os.system("rm -rf /var/log/neutron/*.gz")
os.system("rm -rf /var/log/neutron/*metadata*.log")
os.system("> /var/log/neutron/dhcp-agent.log")
os.system("> /var/log/neutron/server.log")
os.system("> /var/log/neutron/openvswitch-agent.log")
os.system("> /var/log/neutron/dnsmasq.log")

# Increase Neutron quota for network, subnet and port
tenant_id = neutron.get_quotas_tenant()['tenant']['tenant_id']
json = {'quota': {'network': 100000, 'subnet': 100000, 'port': 100000}}
neutron.update_quota(tenant_id, body=json)

mac_base_part = "fa:16:"

def get_next_mac_remaining_part(i):
    m = "{:08X}".format(int("1", 16) + i)
    mac_remaining_part =':'.join(a+b for a,b in zip(m[::2], m[1::2]))
    return mac_remaining_part

if first_dhcp_network == []:
    print "\nWaiting for DHCP network, subnet and ports to be created...."
else:
    print "\nDHCP-network-0 and DHCP-subnet-0 already exist. Waiting for DHCP ports to be created...."
 
# Create a network and subnet if DHCP-network-0 does not exist
if first_dhcp_network == []:
    # Create DHCP test network
    network_name = "DHCP-network-0"
    json = {'network': {'name': network_name, 'admin_state_up': True}}
    netw = neutron.create_network(body=json)
    net_dict = netw['network']
    network_id = net_dict['id']
    network_id_for_dhcp_ports = network_id

    # Create DHCP test subnet
    cidr = "1.0.0.0/16"
    gateway_ip = "1.0.0.1"
    subnet_name = "DHCP-subnet-0"
    json = {'subnets': [{'cidr': cidr,
                     'ip_version': 4,
                     'network_id': network_id,
                     'gateway_ip': gateway_ip,
                     'name': subnet_name}]}
    subnet = neutron.create_subnet(body=json)

# Create DHCP test ports in DHCP-network-0
mac_index = -1
expected_dhcp_port_count = int(dhcp_ports)

# Check if DHCP-network-0 already exists
if first_dhcp_network !=[]:
    network_id_for_dhcp_ports = first_dhcp_network[0]['id']

    # Find number of existing DHCP ports in DHCP-network-0
    f = os.popen("neutron port-list | grep DHCP | wc -l")
    output = f.read()
    existing_dhcp_port_count = output.splitlines()[0]

    expected_dhcp_port_count = int(expected_dhcp_port_count) + int(existing_dhcp_port_count)
    mac_index = int(existing_dhcp_port_count) - 1

for j in range(0, dhcp_ports):
    port_name = "DHCP-port-0" + "-" + str(j)
    port_mac_address = mac_base_part + get_next_mac_remaining_part(mac_index)
    mac_index = mac_index + 1
    json = {'port': {
        'admin_state_up': True,
        'name': port_name,
        'mac_address': port_mac_address,
        'network_id': network_id_for_dhcp_ports}}
    pool.apply_async(t_create_port, (json,))

if "-delete" not in sys.argv:
    while True:
        try:
            f = os.popen("neutron port-list | grep DHCP | wc -l")
            output = f.read()
            output = output.splitlines()
            if output[0] != "0":
                print "{0} : {1} ports found. {2} ports expected".format(str(datetime.now()), output[0], expected_dhcp_port_count)
            if output[0] == str(expected_dhcp_port_count):
                # print "\nDone!\n"
                break
            else:
                time.sleep(5)
        except:
            continue
