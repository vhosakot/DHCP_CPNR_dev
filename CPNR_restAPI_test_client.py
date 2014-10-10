#! /usr/bin/python

########
# Test client to unit-test CPNR_restAPI.py
########

import pprint
from CPNR_restAPI import CPNR_restApi

# CPNR server info
CPNRip = "192.168.122.247"
CPNRport = 8080
CPNRusername = "cpnradmin"
CPNRpassword = "password"

# Create CPNR_restApi object
c = CPNR_restApi(CPNRip, CPNRport, CPNRusername, CPNRpassword)

# Print CPNR_restApi object
test_name = "Print CPNR_restApi object"
print "\n======== {0} ========\n".format(test_name)
print c
print CPNR_restApi(CPNRip, CPNRport, CPNRusername, CPNRpassword)
print dir(c)

# Check docstrings of all methods
test_name = "Check docstrings of all methods"
print "\n======== {0} ========\n".format(test_name)
print c.__doc__
print c.__init__.__doc__
print c.get_dhcp_server.__doc__
print c.get_policies.__doc__
print c.get_policy.__doc__
print c.get_client_classes.__doc__
print c.get_client_class.__doc__
print c.get_vpns.__doc__
print c.get_vpn.__doc__
print c.get_scopes.__doc__
print c.get_scope.__doc__
print c.get_client_entries.__doc__
print c.get_client_entry.__doc__
print c.create_policy.__doc__
print c.create_scope.__doc__
print c.update_dhcp_server.__doc__
print c.create_client_class.__doc__
print c.create_vpn.__doc__
print c.create_client_entry.__doc__
print c.update_policy.__doc__
print c.update_client_class.__doc__
print c.update_vpn.__doc__
print c.update_scope.__doc__
print c.delete_policy.__doc__
print c.delete_client_class.__doc__
print c.delete_vpn.__doc__

# Print all attributes
test_name = "Print all attributes"
print "\n======== {0} ========\n".format(test_name)
print "c.CPNR_server_ip       = {0}".format(c.CPNR_server_ip)
print "c.CPNR_server_port     = {0}".format(c.CPNR_server_port)
print "c.CPNR_server_username = {0}".format(c.CPNR_server_username)
print "c.auth                 = {0}".format(c.auth)
print "c.headers              = {0}".format(c.headers)
print "c.url                  = {0}".format(c.url)

# Get DHCPServer
test_name = "Get DHCPServer"
print "\n======== {0} ========\n".format(test_name)
DHCPServer = c.get_dhcp_server()
pprint.pprint(DHCPServer)

# Update DHCPServer
test_name = "Update DHCPServer"
print "\n======== {0} ========\n".format(test_name)
data = {"name":"DHCP", "clientClass":"True", "clientClassLookupId":"openstack-client-class", "deleteOrphanedLeases":"True"}
print c.update_dhcp_server(data)
pprint.pprint(c.get_dhcp_server())
data = {"name":"DHCP", "clientClass":"False", "clientClassLookupId":"default", "deleteOrphanedLeases":"False"}
print c.update_dhcp_server(data)
pprint.pprint(c.get_dhcp_server())
data = {"name":"DHCP", "clientClass":"True", "clientClassLookupId":"openstack-client-class", "deleteOrphanedLeases":"True"}
print c.update_dhcp_server(data)
pprint.pprint(c.get_dhcp_server())

# Get all policies
test_name = "Get all policies"
print "\n======== {0} ========\n".format(test_name)
Polices = c.get_policies()
pprint.pprint(Polices)

# Get a specific policy
test_name = "Get a specific policy"
print "\n======== {0} ========\n".format(test_name)
Policy = c.get_policy("system_default_policy")
pprint.pprint(Policy)
Policy = c.get_policy("default")
pprint.pprint(Policy)

# Get all ClientClasses
test_name = "Get all ClientClasses"
print "\n======== {0} ========\n".format(test_name)
ClientClasses = c.get_client_classes()
pprint.pprint(ClientClasses)

# Get all VPNs
test_name = "Get all VPNs"
print "\n======== {0} ========\n".format(test_name)
VPNs = c.get_vpns()
pprint.pprint(VPNs)

# Get all scopes
test_name = "Get all scopes"
print "\n======== {0} ========\n".format(test_name)
Scopes = c.get_scopes()
pprint.pprint(Scopes)

# Get all ClientEntries
test_name = "Get all ClientEntries"
print "\n======== {0} ========\n".format(test_name)
ClientEntries = c.get_client_entries()
pprint.pprint(ClientEntries)

# Get a specific ClientEntry
test_name = "Get a specific ClientEntry"
print "\n======== {0} ========\n".format(test_name)
ClientEntry = c.get_client_entry()
pprint.pprint(ClientEntry)

# Create policy object with name, optionList
test_name = "Create policy object with name, optionList"
print "\n======== {0} ========\n".format(test_name)
data = {"name":"policy1", "optionList":{"OptionItem":[{"number":"500","value":"00:09:3a:82"}]}}
print c.create_policy(data)
data = {"name":"policy2", "optionList":{"OptionItem":[{"number":"600","value":"00:09:3a:83"}]}}
print c.create_policy(data)
# Get all policies
pprint.pprint(c.get_policies())

# Get a specific policy
test_name = "Get a specific policy"
print "\n======== {0} ========\n".format(test_name)
# Get policy1
Policy = c.get_policy("policy1")
pprint.pprint(Policy)
# Get policy2
Policy = c.get_policy("policy2")
pprint.pprint(Policy)

# Create scope object with name, subnet, restrictToReservations, vpnId
test_name = "Create scope object with name, subnet, restrictToReservations, vpnId"
print "\n======== {0} ========\n".format(test_name)
data = {"name":"scope1", "subnet":"2.2.2.0/24", "restrictToReservations":"True", "vpnId":"30"}
print c.create_scope(data)
data = {"name":"scope2", "subnet":"3.3.3.0/24", "restrictToReservations":"True", "vpnId":"40"}
print c.create_scope(data)
# Get all scopes
pprint.pprint(c.get_scopes())

# Get a specific scope
test_name = "Get a specific scope"
print "\n======== {0} ========\n".format(test_name)
# Get scope1
Scope = c.get_scope("scope1")
pprint.pprint(Scope)
# Get scope2
Scope = c.get_scope("scope2")
pprint.pprint(Scope)

# Create client class with name, clientLookupId
test_name = "Create client class with name, clientLookupId"
print "\n======== {0} ========\n".format(test_name)
data = {"name":"openstack-client-class", "clientLookupId":"\"(request option 82 \"cisco-vpn-id\")-(request chaddr)\""}
print c.create_client_class(data)
# Get all ClientClasses
pprint.pprint(c.get_client_classes())

# Get a specific client class
test_name = "Get a specific client class"
print "\n======== {0} ========\n".format(test_name)
# Get openstack-client-class
ClientClass = c.get_client_class("openstack-client-class")
pprint.pprint(ClientClass)

# Create VPN with name, id, description, vpnId
test_name = "Create VPN with name, id, description, vpnId"
print "\n======== {0} ========\n".format(test_name)
data = {'name':'418874ff-571b-46e2-a28a-75fe8afcb9e1', 'id':'30', 'description':'418874ff-571b-46e2-a28a-75fe8afcb9e1', 'vpnId':'010203:04050607'}
print c.create_vpn(data)
data = {'name':'418874ff-571b-46e2-a28a-75fe8afcb9e2', 'id':'40', 'description':'418874ff-571b-46e2-a28a-75fe8afcb9e2', 'vpnId':'010203:04050608'}
print c.create_vpn(data)
# Get all VPNs
pprint.pprint(c.get_vpns())

# Get a specific VPN
test_name = "Get a specific VPN"
print "\n======== {0} ========\n".format(test_name)
# Get 418874ff-571b-46e2-a28a-75fe8afcb9e1
VPN = c.get_vpn("418874ff-571b-46e2-a28a-75fe8afcb9e1")
pprint.pprint(VPN)
# Get 418874ff-571b-46e2-a28a-75fe8afcb9e2
VPN = c.get_vpn("418874ff-571b-46e2-a28a-75fe8afcb9e2")
pprint.pprint(VPN)

# Create client entry with name, clientClassName, embeddedPolicy, hostName, reservedAddresses
test_name = "Create client entry with name, clientClassName, embeddedPolicy, hostName, reservedAddresses"
print "\n======== {0} ========\n".format(test_name)
Policy = c.get_policy("policy1")
# data = {'clientClassName': 'openstack-client-class', 'embeddedPolicy': Policy, 'hostName': 'host-name-1', 'name': '010203:04050607-1:2:3:4:5:6', 'reservedAddresses': '2.2.2.2'}

data = {'clientClassName': 'openstack-client-class', 'embeddedPolicy': {"optionList":{"OptionItem":[{"number":"51","value":"00:09:3a:80"}]}}, 'hostName': 'host-name-1', 'name': '010203:04050607-1:2:3:4:5:6', 'reservedAddresses': '2.2.2.2'}

print c.create_client_entry(data)
Policy = c.get_policy("policy2")
data = {'clientClassName': 'openstack-client-class', 'embeddedPolicy': Policy, 'hostName': 'host-name-2', 'name': '010203:04050608-1:2:3:4:5:7', 'reservedAddresses': '3.3.3.3'}
# print c.create_client_entry(data)
# Get all ClientEntries
pprint.pprint(c.get_client_entries())

# Update policy
test_name = "Update policy"
print "\n======== {0} ========\n".format(test_name)
data = {"name":"policy1", "optionList":{"OptionItem":[{"number":"501","value":"00:09:3a:821"}]}}
pprint.pprint(c.get_policy("policy1"))
print c.update_policy("policy1", data)
# Verify if policy1 is updated correctly
pprint.pprint(c.get_policy("policy1"))

# Update client class
test_name = "Update client class"
print "\n======== {0} ========\n".format(test_name)
data = {"name":"openstack-client-class", "clientLookupId":"\"(request option 82 \"cisco-vpn-id1\")-(request chaddr)\""}
pprint.pprint(c.get_client_class("openstack-client-class"))
print c.update_client_class("openstack-client-class", data)
pprint.pprint(c.get_client_class("openstack-client-class"))
data = {"name":"openstack-client-class", "clientLookupId":"\"(request option 82 \"cisco-vpn-id\")-(request chaddr)\""}
print c.update_client_class("openstack-client-class", data)
pprint.pprint(c.get_client_class("openstack-client-class"))

# Update VPN
test_name = "Update VPN"
print "\n======== {0} ========\n".format(test_name)
data = {'name':'418874ff-571b-46e2-a28a-75fe8afcb9e1', 'id':'30', 'description':'418874ff-571b-46e2-a28a-75fe8afcb9e1', 'vpnId':'010203:04056666'}
pprint.pprint(c.get_vpn("418874ff-571b-46e2-a28a-75fe8afcb9e1"))
print c.update_vpn("418874ff-571b-46e2-a28a-75fe8afcb9e1", data)
pprint.pprint(c.get_vpn("418874ff-571b-46e2-a28a-75fe8afcb9e1"))
data = {'name':'418874ff-571b-46e2-a28a-75fe8afcb9e1', 'id':'30', 'description':'418874ff-571b-46e2-a28a-75fe8afcb9e1', 'vpnId':'010203:04050607'}
print c.update_vpn("418874ff-571b-46e2-a28a-75fe8afcb9e1", data)
pprint.pprint(c.get_vpn("418874ff-571b-46e2-a28a-75fe8afcb9e1"))

# Update scope
test_name = "Update scope"
print "\n======== {0} ========\n".format(test_name)
data = {"name":"scope1", "subnet":"22.22.22.0/24", "restrictToReservations":"True", "vpnId":"30"}
pprint.pprint(c.get_scope("scope1"))
print c.update_scope("scope1", data)
pprint.pprint(c.get_scope("scope1"))
data = {"name":"scope1", "subnet":"2.2.2.0/24", "restrictToReservations":"True", "vpnId":"30"}
print c.update_scope("scope1", data)
pprint.pprint(c.get_scope("scope1"))

# Delete policy
test_name = "Delete policy"
print "\n======== {0} ========\n".format(test_name)
# Delete policy1
print c.delete_policy("policy1")
# Delete policy2
print c.delete_policy("policy2")
# Check if policies are deleted correctly
pprint.pprint(c.get_policies())

# Delete client class
test_name = "Delete client class"
print "\n======== {0} ========\n".format(test_name)
print (c.delete_client_class("openstack-client-class"))
# Check if client class is deleted correctly
pprint.pprint(c.get_client_classes())

# Delete VPN
test_name = "Delete VPN"
print "\n======== {0} ========\n".format(test_name)
# Delete 418874ff-571b-46e2-a28a-75fe8afcb9e1
print c.delete_vpn("418874ff-571b-46e2-a28a-75fe8afcb9e1")
# Delete 418874ff-571b-46e2-a28a-75fe8afcb9e2
VPN = c.delete_vpn("418874ff-571b-46e2-a28a-75fe8afcb9e2")
# Check if VPNs are delete correctly
pprint.pprint(c.get_vpns())

print "\n================\n"

