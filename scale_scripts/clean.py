#! /usr/bin/python

import os
import time
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

# Delete neutron logs
os.system("rm -rf /var/log/neutron/*.gz")
os.system("rm -rf /var/log/neutron/*metadata*.log")
os.system("> /var/log/neutron/dhcp-agent.log")
os.system("> /var/log/neutron/server.log")
os.system("> /var/log/neutron/openvswitch-agent.log")

# Delete all ols processes/tests if any
os.system("sudo pkill -f dhcp.py")
os.system("sudo pkill -f dhcp_entries.py")
os.system("sudo pkill -f run_test.sh")
os.system("sudo pkill -f run_test.py")
os.system("sudo pkill -f run_dhcp_tool.py")
os.system("sudo pkill -f device_manager.py")
os.system("sudo pkill -f dh.py")

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
