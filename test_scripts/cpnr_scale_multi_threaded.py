#! /usr/bin/python

# Run the command below to create 100 scopes, 100 VPNs and 100 client entries
# ./cpnr_scale_multi_threaded.py 100

import sys
import pprint
import logging
import thread
import time
from cisco_cpnr_rest_client import CpnrRestClient

logging.basicConfig()

# CPNR server info
CPNRip = "192.168.122.247"
CPNRport = 8080
CPNRusername = "cpnradmin"
CPNRpassword = "password"

# Create CpnrRestClient object
c = CpnrRestClient(CPNRip, CPNRport, CPNRusername, CPNRpassword)

# Update DHCPServer
test_name = "Update DHCPServer"
print "\n======== {0} ========\n".format(test_name)
data = {"name":"DHCP", "clientClass":"True", "clientClassLookupId":"\"openstack-client-class\"", "deleteOrphanedLeases":"True"}
print c.update_dhcp_server(data)
pprint.pprint(c.get_dhcp_server())
# Check _cpnr_reload_needed bool after updating DHCPServer
print "c._cpnr_reload_needed  = {0}".format(c._cpnr_reload_needed)

load = int(sys.argv[1])
interrupt_load = 301

interrupt_scope = False
interrupt_vpn = False
interrupt_ce = False

def create_scopes(load, c):
    # Create scope objects
    test_name = "Create scope objects"
    print "\n======== {0} ========\n".format(test_name)
    a = 0
    b = 0
    global interrupt_load
    global interrupt_scope
    for i in range(1, load + 1):
        subnet = "2." + str(a) + "." + str(b) + ".0/24"
        b = b + 1
        if b == 256:
            b = 0
            a = a + 1
        data = {"name":"scope" + str(i), "subnet":subnet, "restrictToReservations":"True", "vpnId":i}

        if i == interrupt_load:
            interrupt_scope = True
            print "\n\nscope creation interrupted\n\n"
            while interrupt_scope == True:
                pass

        print "scope{0}, return code = {1}".format(i, c.create_scope(data))

    # Get all scopes
    scopes = c.get_scopes()
    print "\n get_scopes() returned the following {0} scopes:\n".format(len(scopes))
    pprint.pprint(scopes)


def create_client_class(c):
    # Create client class with name, clientLookupId
    test_name = "Create client class with name, clientLookupId"
    print "\n======== {0} ========\n".format(test_name)
    data = {"name":"openstack-client-class", "clientLookupId":"(concat (request option 82 151) \"-\" (request chaddr))"}
    print c.create_client_class(data)
    # Get all ClientClasses
    pprint.pprint(c.get_client_classes())


def create_vpns(load, c):
    # Create VPNs with name, id, description, vpnId
    test_name = "Create VPNs with name, id, description, vpnId"
    print "\n======== {0} ========\n".format(test_name)
    global interrupt_load
    global interrupt_vpn

    for i in range(1, load + 1):
        data = {'name':'418874ff-571b-46e2-a28a-75fe8afc' + str(i).zfill(4), 'id':i, 'description':'418874ff-571b-46e2-a28a-75fe8afc' + str(i).zfill(4), 'vpnId':'010203:0405' + str(i).zfill(4)}

        if i == interrupt_load:
            interrupt_vpn = True
            print "\n\nvpn creation interrupted\n\n"
            while interrupt_vpn == True:
                pass

        print "vpn id {0}, return code = {1}".format(i, c.create_vpn(data))

    # Get all VPNs
    vpns = c.get_vpns()
    print "\n get_vpns() returned the following {0} vpns:\n".format(len(vpns))
    pprint.pprint(vpns)


def create_client_entries(load, c):
    # Create client entry objects
    test_name = "Create client entry objects"
    print "\n======== {0} ========\n".format(test_name)
    global interrupt_load
    global interrupt_ce

    for i in range(1, load + 1):
        vpn_name = '418874ff-571b-46e2-a28a-75fe8afc' + str(i).zfill(4)

        if i == interrupt_load:
            interrupt_ce = True
            print "\n\nclient entry creation interrupted\n\n"
            while interrupt_ce == True:
                pass

        while True:
            try:
                vpnId = c.get_vpn(vpn_name)['vpnId']
                break
            except:
                print "Retrying to get VPN...."
                continue
        
        # Generate MAC address and increment it
        m = "{:012X}".format(int("1", 16) + (i-1))
        mac_address =':'.join(a+b for a,b in zip(m[::2], m[1::2]))

        client_class_name = vpnId + "-" + mac_address
        hostname = "host-name-" + str(i)
        tag = "?vpnId=" + c.get_vpn(vpn_name)['id']
        while True:
            try:
                subnet = c.get_scope(tag)[0]['subnet']
                break
            except:
                print "Retrying to get scope...."
                continue

        string_item = subnet[:-4] + "11"
 
        data = {'clientClassName': 'openstack-client-class', 'embeddedPolicy': {'optionList':{'OptionItem':[{'number':'77','value':'00:09:4a:950'}]}}, 'hostName': hostname, 'name': client_class_name, 'reservedAddresses': [{'stringItem':string_item}]}
        print "name = {0}, return code = {1}".format(client_class_name, c.create_client_entry(data))

    # Get all ClientEntries
    ce = c.get_client_entries()
    print "\n get_client_entries() returned the following {0} client entries:\n".format(len(ce))
    pprint.pprint(ce)

thread.start_new_thread(create_scopes, (load, c))
thread.start_new_thread(create_client_class, (c,))
thread.start_new_thread(create_vpns, (load, c))
thread.start_new_thread(create_client_entries, (load, c))

while True:
    if interrupt_scope == True and interrupt_vpn == True and interrupt_ce == True:
        print "\n\nReloading CPNR DHCP Server with {0} scopes, {1} vpns and {2} client entries\n\n".format(interrupt_load-1, interrupt_load-1, interrupt_load-1)
        print c.reload_cpnr_server()
        interrupt_scope = interrupt_vpn = interrupt_ce = False
        while True:
            pass
    time.sleep(1)
