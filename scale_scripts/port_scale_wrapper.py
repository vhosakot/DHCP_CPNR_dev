#! /usr/bin/python

import os
import sys
import time
import argparse
from neutronclient.v2_0 import client as neutron_client

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('p',   help='Number of DHCP ports. A negative value will delete networks, subnets and ports', type=int)
parser.add_argument('-pc', help='Number of DHCP ports to churn per minute. Default is 6', type=int, default=6)
parser.add_argument('-nc', help='Number of DHCP networks to churn per minute. Default is 6', type=int, default=6)

# Parse command line arguments
args = parser.parse_args()
dhcp_ports_count    = args.p
churn_port_count    = args.pc
churn_network_count = args.nc

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

        # Delete all networks and namespaces
        networks = neutron.list_networks()['networks']
        for network in networks:
            if "public-floating-606" in network['name']:
                continue
            ns = "qdhcp-" + str(network['id'])
            neutron.delete_network(network['id'])
            os.system("sudo ip netns delete " + ns + " &> /dev/null")

        # Delete testns test namespace added by device_manager.py
        os.system("./device_manager.py -delete > /dev/null")

    except Exception as e:
        print e
        print "\n ERROR: cleanup() failed\n"

try:
    neutron_credentials = get_neutron_credentials()
    neutron = neutron_client.Client(**neutron_credentials)

    if dhcp_ports_count <= 0:
        # Delete ports, subnets, networks and namespaces
        print "\nDeleting ports, subnets and networks. Please wait...."
        os.system("./device_manager.py -delete")
    
        time.sleep(5)
    
        os.system("./port_create.py -delete")

        time.sleep(5)

        cleanup()

        print "\nDone!\n"

        sys.exit(0)

    # Increase Neutron quota for network, subnet and port
    tenant_id = neutron.get_quotas_tenant()['tenant']['tenant_id']
    json = {'quota': {'network': 100000, 'subnet': 100000, 'port': 100000}}
    neutron.update_quota(tenant_id, body=json)

    # Run scale test using perfdhcp
    cmd = "./port_create.py " + str(dhcp_ports_count)
    os.system(cmd)

    print "\nWaiting 60 seconds....\n"
    time.sleep(60)

    # Check if test namespace testns-DHCP-network-0 exists
    f = os.popen("ip netns list | grep testns-DHCP-network-0")
    output = f.read()
    output = output.splitlines()
    if output != [] and output[0] == "testns-DHCP-network-0":
        # Test namespace testns-DHCP-network-0 exists
        pass
    else:
        os.system("./device_manager.py")
        print "\nWaiting 30 seconds...."
        time.sleep(30)

    cmd = "./run_perfdhcp.py " + str(churn_port_count) + " " + str(churn_network_count)
    os.system(cmd)

except Exception as e:
    print "\n\n ERROR : An exception occurred. Cleaning up.... {0}\n\n".format(e)
    cleanup()
