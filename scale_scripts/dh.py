#! /usr/bin/python

import os
import sys
from multiprocessing import Pool
import time
from datetime import datetime
from neutronclient.v2_0 import client as neutron_client

if len(sys.argv) < 2:
    print "\n Wrong usage\n"
    sys.exit(0)

network_count = 0

if sys.argv[1].isdigit():
    network_count = int(sys.argv[1])
elif sys.argv[1] != "-delete":
    print "\n Wrong usage\n"
    sys.exit(0)

dhcp_ports_per_network = 1

if len(sys.argv) == 3 and sys.argv[1].isdigit() and sys.argv[2].isdigit():
    dhcp_ports_per_network = int(sys.argv[2])
elif len(sys.argv) == 3:
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

# Check if DHCP networks already exist
while True:
    try:
        first_dhcp_network = neutron.list_networks(name="DHCP-network-0")['networks']
        break
    except:
        continue

if len(sys.argv) >= 2 and sys.argv[1] != "-delete" and first_dhcp_network != []:
    print "\n DHCP-network-0 already exists."
    print " Run \'./dh.py -delete\'"
    print " Exiting...\n"
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

cidr_first_byte = 1
cidr_second_byte = 0
mac_base_part = "fa:16:"

print "\nWaiting for DHCP networks, subnets and ports to be created...."

def get_next_mac_remaining_part(i):
    m = "{:08X}".format(int("1", 16) + i)
    mac_remaining_part =':'.join(a+b for a,b in zip(m[::2], m[1::2]))
    return mac_remaining_part

for i in range(0, network_count):

    if cidr_first_byte == 127 or cidr_first_byte == 169 or cidr_first_byte == 172 or cidr_first_byte == 10:
        continue

    # Create DHCP test network
    network_name = "DHCP-network-" + str(i)
    json = {'network': {'name': network_name, 'admin_state_up': True}}
    netw = neutron.create_network(body=json)
    net_dict = netw['network']
    network_id = net_dict['id']

    # Create DHCP test subnet
    cidr = str(cidr_first_byte) + "." + str(cidr_second_byte) + ".0.0/16"
    gateway_ip = str(cidr_first_byte) + "." + str(cidr_second_byte) + ".0.1"
    cidr_second_byte = cidr_second_byte + 1
    if cidr_second_byte == 255:
        cidr_second_byte = 0
        cidr_first_byte = cidr_first_byte + 1

    subnet_name = "DHCP-subnet-" + str(i)
    json = {'subnets': [{'cidr': cidr,
                     'ip_version': 4,
                     'network_id': network_id,
                     'gateway_ip': gateway_ip,
                     'name': subnet_name}]}
    subnet = neutron.create_subnet(body=json)

    mac_index = -1

    # Create DHCP test ports
    for j in range(0, dhcp_ports_per_network):
        port_name = "DHCP-port-" + str(i) + "-" + str(j)
        port_mac_address = mac_base_part + get_next_mac_remaining_part(mac_index)
        mac_index = mac_index + 1
        json = {'port': {
            'admin_state_up': True,
            'name': port_name,
            'mac_address': port_mac_address,
            'network_id': network_id}}
        pool.apply_async(t_create_port, (json,))

if "-delete" not in sys.argv:
    while True:
        try:
            f = os.popen("neutron port-list | grep DHCP | wc -l")
            output = f.read()
            output = output.splitlines()
            if output[0] != "0":
                print "{0} : {1} ports created".format(str(datetime.now()), output[0])
            if output[0] == str(dhcp_ports_per_network * network_count):
                # print "\nDone!\n"
                break
            else:
                time.sleep(5)
        except:
            continue
