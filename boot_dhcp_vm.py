#! /usr/bin/python
# test change 2 
################
#
# This script boots a VM with specific number of DHCP ports requested.
#
# Prerequisites to run this script:
#
# 1. This script boots an Ubuntu VM and expects an Ubuntu image.
#    Hence, run the following commands.
#
#    wget http://uec-images.ubuntu.com/trusty/current/trusty-server-cloudimg-amd64-disk1.img
#
#    glance image-create --name Ubuntu-14.04-trusty-server-x86_64-QCOW2 --disk-format=qcow2 --container-format=bare --is-public=True < trusty-server-cloudimg-amd64-disk1.img
#
# 2. Change the value of the variable public_network_name_in_network_node below in this script
#    to the name of the public network in the network node. In DevStack, the name of the
#    public network in the network node is "public".
#
# Usage is: ./boot_dhcp_vm.py <number_of_DHCP_ports> [-delete]
#
# To boot a VM with 10 DHCP ports:
#
# ./boot_dhcp_vm.py 10
#
# To delete the VM and its 10 DHCP ports:
#
# ./boot_dhcp_vm.py 10 -delete
#
################

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

# Change public_network_name_in_network_node below to the name of the public network in the
# network node. In DevStack, the name of the public network is "public".
public_network_name_in_network_node = "public"

# Get neutron credentials
neutron_credentials = get_neutron_credentials()

# Initialize Neutron client
neutron = neutron_client.Client(**neutron_credentials)

# Get nova credentials
nova_credentials = get_nova_credentials_v2()

# Initialize Nova client
nova = nova_client(**nova_credentials)

# This script creates an Ubuntu VM. Check if the Ubuntu-14.04-trusty-server-x86_64-QCOW2 image exists
nova_image_list = nova.images.list()
expected_ubuntu_image_found = False

for image in nova_image_list:
    if image.name == "Ubuntu-14.04-trusty-server-x86_64-QCOW2":
        expected_ubuntu_image_found = True
        break

if expected_ubuntu_image_found is False:
    print "\n This script creates an Ubuntu VM. No Ubuntu image found."
    print " Run the commands below to create an Ubuntu image."
    print "\n wget http://uec-images.ubuntu.com/trusty/current/trusty-server-cloudimg-amd64-disk1.img"
    print "\n glance image-create --name Ubuntu-14.04-trusty-server-x86_64-QCOW2 --disk-format=qcow2 --container-format=bare --is-public=True < trusty-server-cloudimg-amd64-disk1.img\n"
    sys.exit(0)

# Check if the public network with name public_network_name_in_network_node exists
if neutron.list_networks(name=public_network_name_in_network_node)['networks'] == []:
    print "\n Public network \'{0}\' NOT found in the network node.".format(public_network_name_in_network_node)
    print " Set public_network_name_in_network_node to the name of the public network in the network node.\n"
    sys.exit(0)
 
# Check if DHCP networks and the VM dhcp-scale-VM already exist
first_dhcp_network = neutron.list_networks(name="DHCP-network-0")['networks']
if len(sys.argv) == 2 and first_dhcp_network != []:
    print "\n DHCP-network-0 already exists."
    VM = nova.servers.list(search_opts={'name':'dhcp-scale-VM'})
    if VM != []:
        print " dhcp-scale-VM already exists."
        print " Run \"./boot_dhcp_vm.py {0} -delete\" to delete the VM.".format(len(VM[0].addresses))
    print " Exiting...\n"
    sys.exit(0)

# Delete port, subnet, network
if len(sys.argv) == 3 and sys.argv[2] == "-delete":
    os.system("rm -rf dhcp.pem")
    # Delete floating IP
    floatingip_id = neutron.list_floatingips()['floatingips'][0]['id']
    neutron.delete_floatingip(floatingip_id)
    print "Floating IP deleted"
 
    # neutron router-gateway-clear
    dhcp_scale_router_id = neutron.list_routers(name="dhcp-scale-router")['routers'][0]['id']
    neutron.remove_gateway_router(dhcp_scale_router_id)

    # neutron router-interface-delete
    first_dhcp_subnet_id = neutron.list_subnets(name="DHCP-subnet-0")['subnets'][0]['id']
    json = {"subnet_id": first_dhcp_subnet_id}
    neutron.remove_interface_router(dhcp_scale_router_id, body=json)

    # Delete router dhcp-scale-router
    neutron.delete_router(dhcp_scale_router_id)
    print "dhcp-scale-router deleted"
    # Sleep for 3 seconds so router dhcp-scale-router is deleted
    time.sleep(3)

    # Delete VM
    VM = nova.servers.list(search_opts={'name':'dhcp-scale-VM'})[0] 
    # Start the clock delete VM
    start = time.time()
    nova.servers.delete(VM)
    # Wait until VM is deleted, check once every 5 seconds
    while nova.servers.list(search_opts={'name':'dhcp-scale-VM'}) != []:
        end = time.time()
        print "Waiting for VM to be deleted... Waited {0} seconds".format(end-start)
        time.sleep(5)
        if (end-start) > 600:
            # Delete again if VM is not deleted after 10 mins
            if nova.servers.list(search_opts={'name':'dhcp-scale-VM'}) != []:
                nova.servers.delete(VM)
    # Stop the clock
    end = time.time()
    print "\nVM deleted, took {0} seconds\n".format(end-start)

    # Delete subnet
    subnets = neutron.list_subnets()['subnets']
    for subnet in subnets:
        if "DHCP" in subnet['name']:
            neutron.delete_subnet(subnet['id'])
    print "All subnets deleted"

    # Delete network
    networks = neutron.list_networks()['networks']
    for network in networks:
        if "DHCP" in network['name']:
            neutron.delete_network(network['id'])
    print "All networks deleted"

    print "nova list"
    os.system("nova list") 
    sys.exit(0)

# Increase Neutron quota for network, subnet and port
tenant_id = neutron.get_quotas_tenant()['tenant']['tenant_id']
json = {'quota': {'network': 10000, 'subnet': 10000, 'port': 10000}}
neutron.update_quota(tenant_id, body=json)

cidr_second_byte = 0
cidr_third_byte = 0

# Find id of public network in the network node
dhcp_public_network_id = neutron.list_networks(name=public_network_name_in_network_node)['networks'][0]['id']

# Create public network DHCP-public-network
# json = {'network': {'name': 'DHCP-public-network', 'admin_state_up': True, 'router:external': True}}
# netw = neutron.create_network(body=json)
# net_dict = netw['network']
# dhcp_public_network_id = net_dict['id']

# Create public subnet DHCP-public-subnet for the public network DHCP-public-network
# public_subnet_cidr = "172.24.4.0/24"
# public_subnet_gateway_ip = "172.24.4.1"
# json = {'subnets': [{'cidr': public_subnet_cidr,
#                 'ip_version': 4,
#                 'network_id': dhcp_public_network_id,
#                 'gateway_ip': public_subnet_gateway_ip,
#                 'name': "DHCP-public-subnet",
#                 'enable_dhcp': False}]}
#subnet = neutron.create_subnet(body=json)
#print "DHCP-public-network, DHCP-public-subnet created with {0}".format(public_subnet_cidr)
 
for i in range(0, network_count):
    # Create network
    network_name = "DHCP-network-" + str(i)
    json = {'network': {'name': network_name, 'admin_state_up': True}}
    netw = neutron.create_network(body=json)
    net_dict = netw['network']
    network_id = net_dict['id']
    network_list.append(network_id)

    # Create subnet
    cidr = "20." + str(cidr_second_byte) + "." + str(cidr_third_byte) + ".0/24"
    gateway_ip = "20." + str(cidr_second_byte) + "." + str(cidr_third_byte) + ".1"
    cidr_third_byte = cidr_third_byte + 1
    if cidr_third_byte == 256:
        cidr_third_byte = 0
        cidr_second_byte = cidr_second_byte + 1

    subnet_name = "DHCP-subnet-" + str(i)
    json = {'subnets': [{'cidr': cidr,
                     'ip_version': 4,
                     'network_id': network_id,
                     'gateway_ip': gateway_ip,
                     'name': subnet_name}]}
    subnet = neutron.create_subnet(body=json)
    print "{0}, {1} created with {2}".format(network_name, subnet_name, cidr) 

# Get Nova image and flavor
image = nova.images.find(name="Ubuntu-14.04-trusty-server-x86_64-QCOW2")
flavor = nova.flavors.find(name="m1.large")

nics = []
for network_id in network_list:
    nics.append({'net-id': network_id})

# Run the two nova CLIs below so the VM can be pinged and SSH'ed into
os.system("nova secgroup-add-rule default icmp -1 -1 0.0.0.0/0 2> /dev/null 1> /dev/null")
os.system("nova secgroup-add-rule default tcp 22 22 0.0.0.0/0 2> /dev/null 1> /dev/null")

# nova secgroup-list-rules default

# Create nova keypair needed for SSH
# Run ssh-keygen is needed
os.system("rm -rf dhcp.pem")
os.system("nova keypair-delete dhcp 2> /dev/null")
os.system("nova keypair-add dhcp > dhcp.pem")
os.system("chmod 600 dhcp.pem")

# Start the clock and create VM
print "\nCreating VM with {0} networks\n".format(network_count)
start = time.time()
VM = nova.servers.create(name="dhcp-scale-VM", image=image, flavor=flavor, key_name="dhcp", nics=nics)

# Wait until VM reaches ACTIVE state, check once every 5 seconds
while 1:
    VM = nova.servers.list(search_opts={'name':'dhcp-scale-VM'})[0]
    if VM.status == "ACTIVE":
        # Stop the clock
        end = time.time()
        print "\nVM reached ACTIVE state, took {0} seconds to boot\n".format(end-start)
        break
    else:
        end = time.time()
        print "Waiting... VM still in {0} state, waited {1} seconds".format(VM.status, end-start)
        time.sleep(5)

# Add router before creating floating IP - neutron router-create
json = {"router": {"name": "dhcp-scale-router", "admin_state_up": True}}
result = neutron.create_router(body=json)
dhcp_scale_router_id = neutron.list_routers(name="dhcp-scale-router")['routers'][0]['id']

# neutron router-interface-add
first_dhcp_subnet_id = neutron.list_subnets(name="DHCP-subnet-0")['subnets'][0]['id']
json = {"subnet_id": first_dhcp_subnet_id}
result = neutron.add_interface_router(dhcp_scale_router_id, body=json)

# neutron router-gateway-set
json = {"network_id": dhcp_public_network_id}
result = neutron.add_gateway_router(dhcp_scale_router_id, body=json)

print "dhcp-scale-router created"

# Create floating IP with fixed IP of DHCP-network-0
VM = nova.servers.list(search_opts={'name':'dhcp-scale-VM'})[0]
fixed_ip = VM.addresses['DHCP-network-0'][0]['addr']
first_dhcp_network_id = neutron.list_networks(name="DHCP-network-0")['networks'][0]['id']
ports_in_first_dhcp_network = neutron.list_ports(network_id=first_dhcp_network_id)['ports']
fixed_ip_port_id = ""
for port in ports_in_first_dhcp_network:
    if port['fixed_ips'][0]['ip_address'] == fixed_ip:
        fixed_ip_port_id = port['id']
json = {"floatingip": {"floating_network_id": dhcp_public_network_id, "port_id": fixed_ip_port_id}}
neutron.create_floatingip(body=json)
print "Floating IP created\n"

# Wait and check if floating IP is up for ping and SSH 
print "Checking if floating IP is up. Please wait..."
time.sleep(15)

# Ping the external fixed IP of dhcp-scale-router
dhcp_scale_router_external_fixed_ip = "NULL"
dhcp_scale_router_id = neutron.list_routers(name="dhcp-scale-router")['routers'][0]['id']

if "external_fixed_ips" in neutron.list_routers(name="dhcp-scale-router")['routers'][0]['external_gateway_info']:
    dhcp_scale_router_external_fixed_ip = neutron.list_routers(name="dhcp-scale-router")['routers'][0]['external_gateway_info']['external_fixed_ips'][0]['ip_address']
else:
    neutron_ports = neutron.list_ports()['ports']
    for port in neutron_ports:
        if port['device_id'] == dhcp_scale_router_id and port['device_owner'] == "network:router_gateway":
            dhcp_scale_router_external_fixed_ip = port['fixed_ips'][0]['ip_address']
            break

ping_command1 = "ping -c 8 " + dhcp_scale_router_external_fixed_ip + " > /dev/null"

# Ping 20.0.0.1 and 20.0.0.2 in the namespace of dhcp-scale-router
dhcp_scale_router_namespace = "qrouter-" + dhcp_scale_router_id
ping_command2 = "sudo ip netns exec " + dhcp_scale_router_namespace + " ping -c 8 20.0.0.1" + " > /dev/null"
ping_command3 = "sudo ip netns exec " + dhcp_scale_router_namespace + " ping -c 8 20.0.0.2" + " > /dev/null"

# Ping floating IP
floating_ip_address = neutron.list_floatingips()['floatingips'][0]['floating_ip_address']
ping_command4 = "ping -c 8 " + floating_ip_address

start = time.time()
while 1:
    os.system(ping_command1)
    time.sleep(2)
    os.system(ping_command2)
    time.sleep(2)
    os.system(ping_command3)
    time.sleep(2)
    f = os.popen(ping_command4)
    ping_floating_ip_output = f.read()
    if " 0% packet loss" in ping_floating_ip_output:
        print "\nFloating IP {0} is up!".format(floating_ip_address)
        break
    else:
        end = time.time()
        if (end - start) < 600:
            print "Floating IP not up yet. Still checking..."
            time.sleep(2)
        else:
            print "\nERROR: Floating IP {0} did NOT come up. Waited 10 minutes. "\
            "Please check manually.".format(floating_ip_address)
            break

# For cirros image, SSH username is cirros and password is cubswin:)
# For Fedora image, SSH username is fedora and no password is needed
# For Ubuntu image, SSH username is ubuntu and no password is needed

print "\n  Use below command to SSH into dhcp-scale-VM\n"
print "  ssh -oStrictHostKeyChecking=no -i dhcp.pem ubuntu@" + floating_ip_address + "\n"
