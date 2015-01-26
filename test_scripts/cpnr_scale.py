#! /usr/bin/python

# Run the command below to create 100 scopes, 100 VPNs and 100 client entries
# ./cpnr_scale.py 100

import sys
import pprint
import logging
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

# Create scope objects
test_name = "Create scope objects"
print "\n======== {0} ========\n".format(test_name)
a = 0
b = 0
for i in range(1, load + 1):
    subnet = "2." + str(a) + "." + str(b) + ".0/24"
    b = b + 1
    if b == 256:
        b = 0
        a = a + 1
    data = {"name":"scope" + str(i), "subnet":subnet, "restrictToReservations":"True", "vpnId":i}
    print "scope{0}, return code = {1}".format(i, c.create_scope(data))

# Get all scopes
scopes = c.get_scopes()
print "\n get_scopes() returned the following {0} scopes:\n".format(len(scopes))
pprint.pprint(scopes)
# Check _cpnr_reload_needed bool after creating scope
print "c._cpnr_reload_needed  = {0}".format(c._cpnr_reload_needed)

# Create client class with name, clientLookupId
test_name = "Create client class with name, clientLookupId"
print "\n======== {0} ========\n".format(test_name)
data = {"name":"openstack-client-class", "clientLookupId":"(concat (request option 82 151) \"-\" (request chaddr))"}
print c.create_client_class(data)
# Get all ClientClasses
pprint.pprint(c.get_client_classes())
# Check _cpnr_reload_needed bool after creating client class
print "c._cpnr_reload_needed  = {0}".format(c._cpnr_reload_needed)

# Create VPNs with name, id, description, vpnId
test_name = "Create VPNs with name, id, description, vpnId"
print "\n======== {0} ========\n".format(test_name)

for i in range(1, load + 1):
    data = {'name':'418874ff-571b-46e2-a28a-75fe8afc' + str(i).zfill(4), 'id':i, 'description':'418874ff-571b-46e2-a28a-75fe8afc' + str(i).zfill(4), 'vpnId':'010203:0405' + str(i).zfill(4)}
    print "vpn id {0}, return code = {1}".format(i, c.create_vpn(data))

# Get all VPNs
vpns = c.get_vpns()
print "\n get_vpns() returned the following {0} vpns:\n".format(len(vpns))
pprint.pprint(vpns)
# Check _cpnr_reload_needed bool after creating VPN
print "c._cpnr_reload_needed  = {0}".format(c._cpnr_reload_needed)

# Create client entry objects
test_name = "Create client entry objects"
print "\n======== {0} ========\n".format(test_name)
a = 0
b = 0
_c = 0
d = 0
for i in range(1, load + 1):
    vpn_name = '418874ff-571b-46e2-a28a-75fe8afc' + str(i).zfill(4)
    vpnId = c.get_vpn(vpn_name)['vpnId']

    # Generate MAC address and increment it
    start_mac_address = "de:ae:" + '{0:x}'.format(int(a)) + '{0:x}'.format(int(b)) + ":" + '{0:x}'.format(int(_c)) + '{0:x}'.format(int(d)) + ":00:00"
    client_class_name = vpnId + "-" + start_mac_address
    hostname = "host-name-" + str(i)
    tag = "?vpnId=" + c.get_vpn(vpn_name)['id']
    subnet = c.get_scope(tag)[0]['subnet']
    string_item = subnet[:-4] + "11"
 
    data = {'clientClassName': 'openstack-client-class', 'embeddedPolicy': {'optionList':{'OptionItem':[{'number':'77','value':'00:09:4a:950'}]}}, 'hostName': hostname, 'name': client_class_name, 'reservedAddresses': [{'stringItem':string_item}]}
    print "name = {0}, return code = {1}".format(client_class_name, c.create_client_entry(data))

    if '{0:x}'.format(int(b)) == 'f':
        if '{0:x}'.format(int(a)) == 'f':
            if '{0:x}'.format(int(d)) == 'f':
                _c = _c + 1
                if '{0:x}'.format(int(_c)) == 'f':
                    print "\n  ERROR : Cannot spoof anymore MAC addresses\n"
                    sys.exit(0)
                d = 0
            else:
                d = d + 1
        else:
            a = a + 1
            b = 0
    else:
        b = b + 1

# Get all ClientEntries
ce = c.get_client_entries()
print "\n get_client_entries() returned the following {0} client entries:\n".format(len(ce))
pprint.pprint(ce)
