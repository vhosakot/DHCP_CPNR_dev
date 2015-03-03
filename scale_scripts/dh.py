#! /usr/bin/python

import os
import sys
import pprint
import time
from neutronclient.v2_0 import client as neutron_client
from novaclient.client import Client as nova_client

if len(sys.argv) < 2:
    print "\n\n   Usage is: ./boot_dhcp_vm.py <number_of_DHCP_ports> [-delete]"
    print "   "
    print "   To boot a VM with 10 DHCP ports:"
    print "   ./boot_dhcp_vm.py 10"
    print "   "
    print "   To delete the VM and its 10 DHCP ports:"
    print "   ./boot_dhcp_vm.py 10 -delete\n\n"
    sys.exit(0)

if len(sys.argv) == 3 and sys.argv[2] != "-delete":
    print "\n\n   Usage is: ./boot_dhcp_vm.py <number_of_DHCP_ports> [-delete]"
    print "   "
    print "   To boot a VM with 10 DHCP ports:"
    print "   ./boot_dhcp_vm.py 10"
    print "   "
    print "   To delete the VM and its 10 DHCP ports:"
    print "   ./boot_dhcp_vm.py 10 -delete\n\n"
    sys.exit(0)

network_count = 0

if sys.argv[1].isdigit():
    network_count = int(sys.argv[1])
else:
    print "\n\n   Usage is: ./boot_dhcp_vm.py <number_of_DHCP_ports> [-delete]"
    print "   "
    print "   To boot a VM with 10 DHCP ports:"
    print "   ./boot_dhcp_vm.py 10"
    print "   "
    print "   To delete the VM and its 10 DHCP ports:"
    print "   ./boot_dhcp_vm.py 10 -delete\n\n"
    sys.exit(0)

network_list = []

def get_neutron_credentials():
    d = {}
    d['username'] = os.environ['OS_USERNAME']
    d['password'] = os.environ['OS_PASSWORD']
    d['auth_url'] = os.environ['OS_AUTH_URL']
    d['tenant_name'] = os.environ['OS_TENANT_NAME']
    return d

def get_nova_credentials_v2():
    d = {}
    d['version'] = '2'
    d['username'] = os.environ['OS_USERNAME']
    d['api_key'] = os.environ['OS_PASSWORD']
    d['auth_url'] = os.environ['OS_AUTH_URL']
    d['project_id'] = os.environ['OS_TENANT_NAME']
    return d

public_network_name_in_network_node = "EXTERNAL"

# Get neutron credentials
neutron_credentials = get_neutron_credentials()

# Initialize Neutron client
neutron = neutron_client.Client(**neutron_credentials)

# Get nova credentials
nova_credentials = get_nova_credentials_v2()

# Initialize Nova client
nova = nova_client(**nova_credentials)

# Check if the public network with name public_network_name_in_network_node exists
if neutron.list_networks(name=public_network_name_in_network_node)['networks'] == []:
    print "\n Public network \'{0}\' NOT found in the network node.".format(public_network_name_in_network_node)
    print " Set public_network_name_in_network_node to the name of the public network in the network node.\n"
    sys.exit(0)
 
# Check if DHCP networks already exist
first_dhcp_network = neutron.list_networks(name="DHCP-network-0")['networks']
if len(sys.argv) == 2 and first_dhcp_network != []:
    print "\n DHCP-network-0 already exists."
    DHCP_network_count = len(neutron.list_networks()['networks']) - 1
    print " Run \'./dh.py {0} -delete\'".format(DHCP_network_count)
    print " Exiting...\n"
    sys.exit(0)

# Delete port, subnet, network
if len(sys.argv) == 3 and sys.argv[2] == "-delete":
    # Delete neutron logs
    os.system("rm -rf /var/log/neutron/*.gz")
    os.system("rm -rf /var/log/neutron/*metadata*.log")
    os.system("> /var/log/neutron/dhcp-agent.log")
    os.system("> /var/log/neutron/server.log")
    os.system("> /var/log/neutron/openvswitch-agent.log")

    # Delete all ports
    ports = neutron.list_ports()['ports']
    for port in ports:
        neutron.delete_port(port['id'])
    print "All ports deleted"

    # Delete all DHCP subnets
    subnets = neutron.list_subnets()['subnets']
    for subnet in subnets:
        if "DHCP" in subnet['name']:
            neutron.delete_subnet(subnet['id'])
    print "All subnets deleted"

    # Delete all DHCP networks
    networks = neutron.list_networks()['networks']
    for network in networks:
        if "DHCP" in network['name']:
            neutron.delete_network(network['id'])
    print "All networks deleted"

    # Delete all Linux namespaces
    f = os.popen("ip netns list")
    output = f.read()
    namespaces_list = output.splitlines()
    for namespace in namespaces_list:
        cmd = "sudo ip netns delete " + namespace
        os.system(cmd)

    print "nova list"
    os.system("nova list") 
    sys.exit(0)

# Delete old neutron logs
os.system("rm -rf /var/log/neutron/*.gz")
os.system("rm -rf /var/log/neutron/*metadata*.log")
os.system("> /var/log/neutron/dhcp-agent.log")
os.system("> /var/log/neutron/server.log")
os.system("> /var/log/neutron/openvswitch-agent.log")

# Restart neutron-server
os.system("systemctl restart neutron-server.service")
print "\nWaiting 60 seconds after restarting neutron-server"
time.sleep(60)
print "systemctl status neutron-server.service | grep since"
os.system("systemctl status neutron-server.service | grep since")
print "  "
time.sleep(5)

# Increase Neutron quota for network, subnet and port
tenant_id = neutron.get_quotas_tenant()['tenant']['tenant_id']
json = {'quota': {'network': 50000, 'subnet': 50000, 'port': 50000}}
neutron.update_quota(tenant_id, body=json)

cidr_first_byte = 1
cidr_second_byte = 0

# Find id of public network in the network node
dhcp_public_network_id = neutron.list_networks(name=public_network_name_in_network_node)['networks'][0]['id']

for i in range(0, network_count):

    if cidr_first_byte == 127 or cidr_first_byte == 169 or cidr_first_byte == 172:
        continue
 
    # Create network
    network_name = "DHCP-network-" + str(i)
    json = {'network': {'name': network_name, 'admin_state_up': True}}
    netw = neutron.create_network(body=json)
    net_dict = netw['network']
    network_id = net_dict['id']
    network_list.append(network_id)

    # Create subnet
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

    # Create port
    port_name = "DHCP-port-" + str(i)
    json = {'port': {
        'admin_state_up': True,
        'name': port_name,
        'network_id': network_id}}
    port = neutron.create_port(body=json)

    print "{0}, {1}, {2} created with {3}".format(network_name, subnet_name, port_name, cidr)
