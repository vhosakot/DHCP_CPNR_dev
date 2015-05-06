#! /usr/bin/python

import os
import sys
import time
import argparse
from neutronclient.v2_0 import client as neutron_client

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('p',   help='Number of DHCP ports per network.', type=int)
parser.add_argument('-n',  help='Number of DHCP networks. Default is 1.', type=int, default=1)
parser.add_argument('-pc', help='Port-churn rate per minute. Default is 5.', type=int, default=5)
parser.add_argument('-nc', help='Network-churn rate per minute. Default is 3.', type=int, default=3)

# Parse command line arguments
args = parser.parse_args()
dhcp_ports_per_network = args.p
network_count          = args.n
port_churn_rate        = args.pc
network_churn_rate     = args.nc

def get_neutron_credentials():
    d = {}
    d['username'] = os.environ['OS_USERNAME']
    d['password'] = os.environ['OS_PASSWORD']
    d['auth_url'] = os.environ['OS_AUTH_URL']
    d['tenant_name'] = os.environ['OS_TENANT_NAME']
    return d

def cleanup():
    try:
        neutron_credentials = get_neutron_credentials()
        neutron = neutron_client.Client(**neutron_credentials)

        # Kill perfdhcp if running
        os.system("sudo pkill -f perfdhcp")
        time.sleep(1)
        os.system("sudo pkill -f perfdhcp")

        # Delete neutron logs
        os.system("rm -rf /var/log/neutron/*.gz")
        os.system("rm -rf /var/log/neutron/*metadata*.log")
        os.system("> /var/log/neutron/dhcp-agent.log")
        os.system("> /var/log/neutron/server.log")
        os.system("> /var/log/neutron/openvswitch-agent.log")
        os.system("> /var/log/neutron/dnsmasq.log")
 
        # Delete all ports
        ports = neutron.list_ports()['ports']
        for port in ports:
            neutron.delete_port(port['id'])

        # Delete all subnets
        subnets = neutron.list_subnets()['subnets']
        for subnet in subnets:
            if "public-floating-606-subnet" in subnet['name']:
                continue
            neutron.delete_subnet(subnet['id'])

        # Delete all networks
        networks = neutron.list_networks()['networks']
        for network in networks:
            if "public-floating-606" in network['name']:
                continue
            ns = "qdhcp-" + str(network['id'])
            neutron.delete_network(network['id'])
            os.system("sudo ip netns delete " + ns + " &> /dev/null")

        # Delete testns test namespace added by device_manager.py
        os.system("./device_manager.py -delete > /dev/null")

    except:
        print "\n ERROR: cleanup() failed\n"

# Cleanup unwanted ports, subnets, networks and namespaces
cleanup()

try:
    neutron_credentials = get_neutron_credentials()
    neutron = neutron_client.Client(**neutron_credentials)

    # Increase Neutron quota for network, subnet and port
    tenant_id = neutron.get_quotas_tenant()['tenant']['tenant_id']
    json = {'quota': {'network': 100000, 'subnet': 100000, 'port': 100000}}
    neutron.update_quota(tenant_id, body=json)

    # Run scale test using perfdhcp
    cmd = "./dh.py " + str(network_count) + " " + str(dhcp_ports_per_network)
    os.system(cmd)

    print "\nWaiting 60 seconds....\n"
    time.sleep(60)

    os.system("./device_manager.py")

    print "\nWaiting 30 seconds...."
    time.sleep(30)

    cmd = "./run_perfdhcp.py " + str(port_churn_rate) + " " + str(network_churn_rate)
    os.system(cmd)

    # Delete ports, subnets, networks and namespaces after scale test
    print "Test ended. Deleting ports, subnets and networks. Please wait....\n"
    os.system("./device_manager.py -delete")

    time.sleep(30)

    os.system("./dh.py -delete")
    print "\nDone!\n"

except:
    cleanup()
