#! /usr/bin/python

import os
import logging
import sys
from neutron.agent.common import config
from neutron.agent.linux import dhcp
from neutron.agent import dhcp_agent
from neutron import context
from neutron.common import topics
from neutronclient.v2_0 import client as neutron_client
from novaclient.client import Client as nova_client

# logging.basicConfig(level=logging.DEBUG)

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

if len(sys.argv) == 2 and sys.argv[1] == "-delete":
    f = os.popen("ovs-vsctl list-ports br-int | grep tap")
    output = f.read()
    test_tap_interface_list = output.splitlines()
    for test_tap_interface in test_tap_interface_list:
        cmd = "ovs-vsctl del-port " + test_tap_interface
        print cmd
        os.system(cmd)
    sys.exit(0)

dhcp_agent.register_options()
dhcp_agent.cfg.CONF(project='neutron')
conf = dhcp_agent.cfg.CONF
root_helper = config.get_root_helper(conf)
ctx = context.get_admin_context_without_session()
plugin = dhcp_agent.DhcpPluginApi(topics.PLUGIN, ctx, conf.use_namespaces)
conf.interface_driver = "neutron.agent.linux.interface.OVSInterfaceDriver"

network_list = neutron.list_networks()
DHCP_network_count = len(network_list['networks']) - 1

for i in range(0, DHCP_network_count):
    test_device = dhcp.DeviceManager(conf, root_helper, plugin)
    test_device.test = True
    network_name = "DHCP-network-" + str(i)
    network_id = neutron.list_networks(name=network_name)['networks'][0]['id']
    network = plugin.get_network_info(network_id)
    test_tap_interface = test_device.setup(network, reuse_existing=False)
    print "Added 2nd test tap interface {0} in namespace of {1}".format(test_tap_interface, network_name)

    # Check if iface(2nd tap interface added by DeviceManager)
    # exists in the namespace
    print "\nChecking if 2nd tap interface added by DeviceManager exists in namespace\n"
    cmd = "neutron port-list | grep " + test_tap_interface[3:]
    f = os.popen(cmd)
    tap_port_id = f.read().splitlines()[0].split()[1]
    tap_port_network_id = neutron.list_ports(id=tap_port_id)['ports'][0]['network_id']

    cmd = "sudo ip netns exec " + "qdhcp-" + tap_port_network_id + " ip a"
    print cmd
    f = os.popen(cmd)
    output = f.read().splitlines()
    for line in output:
        print line

    print "\novs-vsctl show"
    f = os.popen("ovs-vsctl show")
    output = f.read().splitlines()
    for line in output:
        print line

    print "\n"
