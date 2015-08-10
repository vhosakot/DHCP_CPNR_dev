#! /usr/bin/python

#####################################################################
# Usage :
# ./network_scale_wrapper.py -h
# usage: network_scale_wrapper.py [-h] [-p P] [-pc PC] [-nc NC] n
# 
# positional arguments:
#   n           Number of DHCP networks. A negative value will delete networks,
#               subnets and ports
# 
# optional arguments:
#   -h, --help  show this help message and exit
#   -p P        Number of DHCP ports per network. Default is 3 DHCP ports per
#               network
#   -pc PC      Number of DHCP ports to churn per minute. Default is 6
#   -nc NC      Number of DHCP networks to churn per minute. Default is 6
# 
# Example to run network-scaling with 100 DHCP networks each with 4 DHCP ports (400 total DHCP ports) with 
# 6 DHCP ports churned every minute and 6 DHCP networks churned every minute.
#  
# ./network_scale_wrapper.py 100 -p 4
#  
# Example to run network-scaling with 200 DHCP networks each with 5 DHCP ports (1000 total DHCP ports) with
# 7 DHCP ports churned every minute and 8 DHCP networks churned every minute.
#
# ./network_scale_wrapper.py 200 -p 5 -pc 7 -nc 8
# 
#####################################################################

import os
import sys
import time
import argparse
from neutronclient.v2_0 import client as neutron_client

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('n',   help='Number of DHCP networks. A negative value will delete networks, subnets and ports', type=int)
parser.add_argument('-p',   help='Number of DHCP ports per network. Default is 3 DHCP ports per network', type=int, default=3)
parser.add_argument('-pc', help='Number of DHCP ports to churn per minute. Default is 6', type=int, default=6)
parser.add_argument('-nc', help='Number of DHCP networks to churn per minute. Default is 6', type=int, default=6)

# Parse command line arguments
args = parser.parse_args()
dhcp_networks_count    = args.n
dhcp_ports_per_network = args.p
churn_port_count       = args.pc
churn_network_count    = args.nc

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
        # os.system("> /var/log/neutron/dhcp-agent.log")
        os.system("> /var/log/neutron/server.log")
        os.system("> /var/log/neutron/openvswitch-agent.log")
        os.system("> /var/log/neutron/dnsmasq.log")
        os.system("> /var/log/neutron/dhcp-relay.log")
        os.system("> /var/log/neutron/dns-relay.log")
 
        exclude_networks = []
        exclude_subnets  = []
        exclude_ports    = []
        base_networks    = []

        # Enter names of the networks that must not be deleted when cleanup
        # is done by this script. The subnets and ports of the network
        # names in the list existing_network_names below will also not be
        # deleted when cleanup is done by this script.

        existing_network_names = ["EXTERNAL", "pnr-network"]
        
        for existing_network in existing_network_names:
            base_networks.append(neutron.list_networks(name=existing_network)['networks'])
        
        for base_nw in base_networks:
            if base_nw != []:
                exclude_networks.append(base_nw[0]['id'])
                if base_nw[0]['subnets'] != []:
                    exclude_subnets.append(base_nw[0]['subnets'][0])
                ports_in_network = neutron.list_ports(network_id=base_nw[0]['id'])['ports']
                if ports_in_network != []:
                    for port in ports_in_network:
                        exclude_ports.append(port['id'])
        
        # Delete all ports
        ports = neutron.list_ports()['ports']
        for port in ports:
            if port['id'] in exclude_ports:
                continue
            neutron.delete_port(port['id'])

        # Delete all subnets
        subnets = neutron.list_subnets()['subnets']
        for subnet in subnets:
            if subnet['id'] in exclude_subnets:
                continue
            neutron.delete_subnet(subnet['id'])

        # Delete all networks and namespaces
        networks = neutron.list_networks()['networks']
        for network in networks:
            if network['id'] in exclude_networks:
                continue
            ns = "qdhcp-" + str(network['id'])
            neutron.delete_network(network['id'])
            os.system("sudo ip netns delete " + ns + " &> /dev/null")

        # Delete testns test namespace added by device_manager.py
        os.system("./device_manager.py -delete > /dev/null")

        # Delete configs (scopes, VPNs, client entries, CCM zones, DNS views, etc) on CPNR
        f = os.popen("grep dhcp_server_addr /etc/neutron/dhcp_agent.ini")
        output = f.read()
        cpnr_ip = output.splitlines()
        if cpnr_ip != []:
            cpnr_ip = cpnr_ip[0].split("=")[1]
        #     os.system("./deleteall.py " + cpnr_ip)

        # Clean DHCP stats on CPNR
        cmd = "ssh cloud-user@" + cpnr_ip + " \"/opt/nwreg2/local/usrbin/nrcmd -N cpnradmin -P cpnradmin \"dhcp resetStats\"\""
        os.system(cmd)
        time.sleep(3)
        os.system(cmd)

    except Exception as e:
        print e
        print "\n ERROR: cleanup() failed\n"

try:
    neutron_credentials = get_neutron_credentials()
    neutron = neutron_client.Client(**neutron_credentials)

    if dhcp_networks_count <= 0:
        # Delete ports, subnets, networks and namespaces
        print "\nDeleting ports, subnets and networks. Please wait...."
        os.system("./device_manager.py -delete")
    
        time.sleep(5)
    
        os.system("./network_create.py -delete")

        time.sleep(5)

        cleanup()

        print "\nCleanup done!\n"

        sys.exit(0)

    # Delete networks, subnets and ports if any created in previous run
    cleanup()

    # Increase Neutron quota for network, subnet and port
    tenant_id = neutron.get_quotas_tenant()['tenant']['tenant_id']
    json = {'quota': {'network': 100000, 'subnet': 100000, 'port': 100000}}
    neutron.update_quota(tenant_id, body=json)

    # Run scale test using perfdhcp
    cmd = "./network_create.py " + str(dhcp_networks_count) + " " + str(dhcp_ports_per_network)
    os.system(cmd)

    print "\nWaiting 120 seconds after creating {0} networks each with {1} ports....\n".format(dhcp_networks_count, dhcp_ports_per_network)
    time.sleep(120)

    os.system("systemctl restart neutron-dhcp-agent.service")
    print "Waiting 120 seconds after restarting neutron-dhcp-agent.service....\n"
    time.sleep(120)

    os.system("./device_manager.py")
    print "\nWaiting 40 seconds...."
    time.sleep(30)

    os.system("./device_manager.py")
    time.sleep(5)

    os.system("./device_manager.py")
    time.sleep(5)

    cmd = "./run_perfdhcp.py " + str(churn_port_count) + " " + str(churn_network_count)
    os.system(cmd)

except Exception as e:
    print "\n\n ERROR : An exception occurred. Cleaning up.... {0}\n\n".format(e)
    cleanup()
