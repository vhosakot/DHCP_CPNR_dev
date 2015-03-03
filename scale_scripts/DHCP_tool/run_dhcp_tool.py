#! /usr/bin/python

import os
import sys
from neutronclient.v2_0 import client as neutron_client
from novaclient.client import Client as nova_client

if len(sys.argv) < 2:
    print "\n\n   ERROR : Invalid input \n\n"
    sys.exit(0)

if sys.argv[1].isdigit():
    ports_per_network = int(sys.argv[1])
else:
    print "\n\n   ERROR : Invalid input \n\n"
    sys.exit(0)

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

neutron_credentials = get_neutron_credentials()
neutron = neutron_client.Client(**neutron_credentials)
nova_credentials = get_nova_credentials_v2()
nova = nova_client(**nova_credentials)
a = 0
b = 0
network_list = neutron.list_networks()
DHCP_network_count = len(network_list['networks']) - 1

if len(sys.argv) == 3 and sys.argv[2] == "-delete":
    for i in range(0, DHCP_network_count):
        subnet_name = "DHCP-subnet-" + str(i)
        spoof_start_ip = neutron.list_subnets(name=subnet_name)['subnets'][0]['allocation_pools'][0]['start']
        spoof_start_ip = spoof_start_ip[:-1]
        spoof_start_ip = spoof_start_ip + "5"

        spoof_start_mac_address = "de:ae:" + '{0:x}'.format(int(a)) + '{0:x}'.format(int(b)) + ":00:00:00"
        if '{0:x}'.format(int(b)) == 'f':
            if '{0:x}'.format(int(a)) == 'f':
                print "\n  ERROR: Cannot spoof anymore MAC addresses\n"
                sys.exit(0)
            a = a + 1
            b = 0
        else:
            b = b + 1

        cmd = "python dhcp_entries.py -m " + spoof_start_mac_address + "@" + spoof_start_ip + ":" + str(ports_per_network) + "@DHCP-network-" + str(i) + " -d"
        print cmd
        os.system(cmd)
        print "Deleted {0} test DHCP ports from {1}".format(ports_per_network, "DHCP-network-" + str(i))
    sys.exit(0)

for i in range(0, DHCP_network_count):
    subnet_name = "DHCP-subnet-" + str(i)
    spoof_start_ip = neutron.list_subnets(name=subnet_name)['subnets'][0]['allocation_pools'][0]['start']
    spoof_start_ip = spoof_start_ip[:-1]
    spoof_start_ip = spoof_start_ip + "5"

    spoof_start_mac_address = "de:ae:" + '{0:x}'.format(int(a)) + '{0:x}'.format(int(b)) + ":00:00:00"
    if '{0:x}'.format(int(b)) == 'f':
        if '{0:x}'.format(int(a)) == 'f':
            print "\n  ERROR: Cannot spoof anymore MAC addresses\n"
            sys.exit(0)
        a = a + 1
        b = 0
    else:
        b = b + 1

    cmd = "python dhcp_entries.py -m " + spoof_start_mac_address + "@" + spoof_start_ip + ":" + str(ports_per_network) + "@DHCP-network-" + str(i)
    print cmd
    os.system(cmd)
    print "Added {0} test DHCP ports to {1}".format(ports_per_network, "DHCP-network-" + str(i))
