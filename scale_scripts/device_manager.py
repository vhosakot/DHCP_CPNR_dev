#! /usr/bin/python

# The functions 'get_device_id' and 'setup' in the DeviceManager class must be modified in
# /usr/lib/python2.7/site-packages/neutron/agent/linux/dhcp.py before running this script

# Usage   : ./device_manager.py [-delete]
# Example : ./device_manager.py
# Example : ./device_manager.py -delete

import os
import sys
import time
from multiprocessing import Pool
from neutron.agent.common import config
from neutron.agent.linux import dhcp
from neutron.agent import dhcp_agent
from neutron import context
from neutron.common import topics
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

if len(sys.argv) == 2 and sys.argv[1] == "-delete":
    f = os.popen("ip netns list | grep testns-DHCP")
    output = f.read()
    test_ns_list = output.splitlines()
    for test_ns in test_ns_list:
        os.system("ip netns delete " + test_ns)

    f = os.popen("ovs-vsctl list-ports br-int | grep tap")
    output = f.read()
    test_tap_interface_list = output.splitlines()
    for test_tap_interface in test_tap_interface_list:
        cmd = "ovs-vsctl del-port " + test_tap_interface
        # print cmd
        os.system(cmd)
    sys.exit(0)

def t_create_testns(testns_name, network):
    try:
        neutron_credentials = get_neutron_credentials()
        neutron = neutron_client.Client(**neutron_credentials)
        dhcp_agent.register_options()
        dhcp_agent.cfg.CONF(project='neutron')
        conf = dhcp_agent.cfg.CONF
        root_helper = config.get_root_helper(conf)
        ctx = context.get_admin_context_without_session()
        plugin = dhcp_agent.DhcpPluginApi(topics.PLUGIN, ctx, conf.use_namespaces)
        conf.interface_driver = "neutron.agent.linux.interface.OVSInterfaceDriver"

        a = os.system("ip netns add " + testns_name)
        if a != 0:
            return
        time.sleep(2)

        test_device = dhcp.DeviceManager(conf, root_helper, plugin)
        test_device.test = True
        pnetwork = plugin.get_network_info(network['id'])
        test_tap_interface = test_device.setup(pnetwork, reuse_existing=False, test_tap=True,
                                               test_tap_mac="ee:ff:ff:ff:ff:ef",
                                               test_ns=testns_name)
        subnet_id = network['subnets'][0]

        while True:
            try:
                subnet = neutron.list_subnets(id=subnet_id)['subnets'][0]
                break
            except:
                continue

        gateway_ip = subnet['gateway_ip']
        os.system("sudo ip netns exec " + testns_name + " ifconfig " + test_tap_interface + " " + gateway_ip + " netmask 255.255.255.0 up")
        os.system("sudo ip netns exec " + testns_name + " ifconfig " + test_tap_interface + " up")
        print "\nAdded test tap interface {0} ({1}) in namespace {2}".format(test_tap_interface, gateway_ip, testns_name)

        time.sleep(2)

        try:
            f = os.popen("sudo ip netns exec qdhcp-" + str(network['id']) + " ip a | grep inet | grep -v 'inet6\|127\|169'")
            output = f.read().splitlines()[0]
            ping_ip = output.split()[1].split('/')[0]
        except Exception as e:
            print "\n ERROR : Error when running command in namespace {0}".format("qdhcp-" + str(network['id']))
            print e
            return

        f = os.popen("sudo ip netns exec " + testns_name + " ping -c 5 " + ping_ip)
        output = f.read()
        ping_output = output.splitlines()
        ping_output = ping_output[len(ping_output) - 2]
        # if " 0% packet loss" not in ping_output:
            # print "\n ERROR: Cannot ping {0} from test namespace {1}\n".format(ping_ip, testns_name)

        f = os.popen("sudo ip netns exec " + testns_name + " ping -c 5 " + ping_ip)
        output = f.read()
        ping_output = output.splitlines()
        ping_output = ping_output[len(ping_output) - 2]
        # if " 0% packet loss" not in ping_output:
            # print "\n ERROR: Cannot ping {0} from test namespace {1}\n".format(ping_ip, testns_name)
    
        f = os.popen("sudo ip netns exec " + testns_name + " ping -c 5 " + ping_ip)
        output = f.read()
        ping_output = output.splitlines()
        ping_output = ping_output[len(ping_output) - 2]
        # if " 0% packet loss" not in ping_output:
            # print "\n ERROR: Cannot ping {0} from test namespace {1}\n".format(ping_ip, testns_name)
    except Exception as e:
        print "\n ERROR : An exception occurred when creating test namespace {0} for {1}".format(testns_name,  network['name'])
        print e

pool = Pool(processes=100)

while True:
    try:
        networks = neutron.list_networks()['networks']
        break
    except:
        continue

testns_count = 0

for network in networks:
    if "DHCP" in network['name']:
        testns_name = "testns-" + network['name']

        # Check if namespace testns_name already exists
        f = os.popen("ip netns | grep -w " + testns_name)
        output = f.read()
        output = output.splitlines()
        if output != [] and output [0] == testns_name:
            # print testns_name + " already found"
            continue
        else:
            pool.apply_async(t_create_testns, (testns_name, network))
            testns_count = testns_count + 1

if testns_count > 0:
    print "\nWaiting for test namespaces to be created for perfDHCP...."
    pool.close()
    pool.join()
    print "\n{0} test namespaces created for perfDHCP\n".format(testns_count)
