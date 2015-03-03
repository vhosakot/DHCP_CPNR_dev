#! /usr/bin/python

import os
import sys
import time
from neutronclient.v2_0 import client as neutron_client
from novaclient.client import Client as nova_client

if len(sys.argv) < 2:
    print "\n\n   Usage is: ./dhcp_scale_wrapper.py <number_of_DHCP_ports> [-delete]"
    print "   "
    sys.exit(0)

network_count = 0
ports_per_network = 0

if sys.argv[1].isdigit():
    ports_per_network = int(sys.argv[1])
else:
    print "\n\n   Usage is: ./dhcp_scale_wrapper.py <number_of_DHCP_ports> [-delete]"
    print "   "
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

first_dhcp_network = neutron.list_networks(name="DHCP-network-0")['networks']
if len(sys.argv) == 2 and first_dhcp_network != []:
    print "\n DHCP network already exists."
    DHCP_network_count = len(neutron.list_networks()['networks']) - 1
    DHCP_port_count = len(neutron.list_ports()['ports'])
    print " # of DHCP networks = {0}\n # of DHCP ports per network = {1}".format(DHCP_network_count, (DHCP_port_count/DHCP_network_count) - 3)
    print " Run \'./dhcp_scale_wrapper.py <number_of_DHCP_ports> -delete\'"
    print " Exiting...\n"
    sys.exit(0)

if len(sys.argv) == 3 and sys.argv[2] == "-delete":
    try:
        os.chdir("DHCP_tool")
        cmd = "./run_dhcp_tool.py " + str(ports_per_network) + " -delete"
        os.system(cmd)

        print "\nSleeping for 30 secs after deleting all the test ports\n"
        time.sleep(30)

        os.chdir("..")
        os.system("./device_manager.py -delete")

        time.sleep(5)

        network_count = 1
        cmd = "./dh.py " + str(network_count) + " -delete"
        os.system(cmd)

        print "\nSleeping for 30 secs after deleting all networks\n"
        time.sleep(30)

        sys.exit(0)

    except Exception as inst:
        print "\n\n An exception occurred during deletion\n\n"
        print type(inst)
        print inst.args
        print inst

        # Delete neutron logs
        os.system("rm -rf /var/log/neutron/*.gz")
        os.system("rm -rf /var/log/neutron/*metadata*.log")
        os.system("> /var/log/neutron/dhcp-agent.log")
        os.system("> /var/log/neutron/server.log")
        os.system("> /var/log/neutron/openvswitch-agent.log")

        # Delete all OVS tap interfaces
        f = os.popen("ovs-vsctl list-ports br-int | grep tap")
        output = f.read()
        test_tap_interface_list = output.splitlines()
        for test_tap_interface in test_tap_interface_list:
            cmd = "ovs-vsctl del-port " + test_tap_interface
            print cmd
            os.system(cmd)
    
        time.sleep(5)

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

        print "\nSleeping for 30 secs after deleting all networks\n"
        time.sleep(30)

        sys.exit(0)

try:
    # Delete all old processes/tests if any
    for i in range(0, 5):
        os.system("sudo pkill -f dhcp.py")
        os.system("sudo pkill -f dhcp_entries.py")
        os.system("sudo pkill -f run_test.sh")
        os.system("sudo pkill -f run_test.py")
        os.system("sudo pkill -f run_dhcp_tool.py")
        os.system("sudo pkill -f device_manager.py")
        os.system("sudo pkill -f dh.py")
        time.sleep(3)

    # Delete all old OVS tap interfaces if any
    f = os.popen("ovs-vsctl list-ports br-int | grep tap")
    output = f.read()
    test_tap_interface_list = output.splitlines()
    for test_tap_interface in test_tap_interface_list:
        cmd = "ovs-vsctl del-port " + test_tap_interface
        print cmd
        os.system(cmd)

    time.sleep(5)

    # Delete all old ports if any
    ports = neutron.list_ports()['ports']
    for port in ports:
        neutron.delete_port(port['id'])

    # Delete all old DHCP subnets if any
    subnets = neutron.list_subnets()['subnets']
    for subnet in subnets:
        if "DHCP" in subnet['name']:
            neutron.delete_subnet(subnet['id'])

    # Delete all old DHCP networks if any
    networks = neutron.list_networks()['networks']
    for network in networks:
        if "DHCP" in network['name']:
            neutron.delete_network(network['id'])

    # Delete all old Linux namespaces if any
    f = os.popen("ip netns list")
    output = f.read()
    namespaces_list = output.splitlines()
    for namespace in namespaces_list:
        cmd = "sudo ip netns delete " + namespace
        os.system(cmd)

    time.sleep(5)

    network_count = 1
    cmd = "./dh.py " + str(network_count)
    os.system(cmd)

    print "\n Sleeping 10 seconds after creating networks........\n"
    time.sleep(10)

    os.system("./device_manager.py")

    print "\n Sleeping 10 seconds after DeviceManager........\n"
    time.sleep(10)

    os.chdir("DHCP_tool")
    cmd = "./run_dhcp_tool.py " + str(ports_per_network)
    os.system(cmd)

    print "\n Sleeping 60 seconds after adding DHCP test ports........\n"
    time.sleep(60)

    churn_ports_per_network = 2
    churn_sleep_time = 60

    if len(sys.argv) >= 3 and sys.argv[2].isdigit():
        churn_ports_per_network = int(sys.argv[2])

    if len(sys.argv) == 4 and sys.argv[3].isdigit():
        churn_sleep_time = int(sys.argv[3])

    cmd = "./run_test.py " + str(churn_ports_per_network) + " " + str(churn_sleep_time)

    os.system(cmd)
    os.chdir("..")

except Exception as inst:
    print "\n\n An exception occurred\n\n"
    print type(inst)
    print inst.args
    print inst

    # Delete neutron logs
    os.system("rm -rf /var/log/neutron/*.gz")
    os.system("rm -rf /var/log/neutron/*metadata*.log")
    os.system("> /var/log/neutron/dhcp-agent.log")
    os.system("> /var/log/neutron/server.log")
    os.system("> /var/log/neutron/openvswitch-agent.log")

    # Delete all OVS tap interfaces
    f = os.popen("ovs-vsctl list-ports br-int | grep tap")
    output = f.read()
    test_tap_interface_list = output.splitlines()
    for test_tap_interface in test_tap_interface_list:
        cmd = "ovs-vsctl del-port " + test_tap_interface
        os.system(cmd)

    time.sleep(5)

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

    print "\nSleeping for 30 secs after deleting all networks\n"
    time.sleep(30)
