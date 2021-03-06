#! /usr/bin/python

# Copyright 2014 Cisco Systems, Inc.  All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

########
# Test client to unit-test cisco_cpnr_rest_client.py 
########

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

# Print CpnrRestClient object
test_name = "Print CpnrRestClient object"
print "\n======== {0} ========\n".format(test_name)
print c
print CpnrRestClient(CPNRip, CPNRport, CPNRusername, CPNRpassword)
print dir(c)

# Check docstrings of all methods
test_name = "Check docstrings of all methods"
print "\n======== {0} ========\n".format(test_name)
print c.__doc__
print c.__init__.__doc__
print c.get_cpnr_version.__doc__
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
print c.update_client_entry.__doc__
print c.delete_policy.__doc__
print c.delete_client_class.__doc__
print c.delete_vpn.__doc__
print c.delete_scope.__doc__
print c.delete_client_entry.__doc__
print c.get_leases.__doc__
print c.reload_cpnr_server.__doc__

# Print all attributes
test_name = "Print all attributes"
print "\n======== {0} ========\n".format(test_name)
print "c.CPNR_server_ip       = {0}".format(c.CPNR_server_ip)
print "c.CPNR_server_port     = {0}".format(c.CPNR_server_port)
print "c.CPNR_server_username = {0}".format(c.CPNR_server_username)
print "c.auth                 = {0}".format(c.auth)
print "c.headers              = {0}".format(c.headers)
print "c.url                  = {0}".format(c.url)
print "c._cpnr_reload_needed  = {0}".format(c._cpnr_reload_needed)
print "c.timeout              = {0}".format(c.timeout)

# Get CPNR version
test_name = "Get CPNR version"
print "\n======== {0} ========\n".format(test_name)
print c.get_cpnr_version()

# Get DHCPServer
test_name = "Get DHCPServer"
print "\n======== {0} ========\n".format(test_name)
DHCPServer = c.get_dhcp_server()
pprint.pprint(DHCPServer)

# Update DHCPServer
test_name = "Update DHCPServer"
print "\n======== {0} ========\n".format(test_name)
data = {"name":"DHCP", "clientClass":"True", "clientClassLookupId":"\"openstack-client-class\"", "deleteOrphanedLeases":"True"}
print c.update_dhcp_server(data)
pprint.pprint(c.get_dhcp_server())
data = {"name":"DHCP", "clientClass":"False", "clientClassLookupId":"\"default\"", "deleteOrphanedLeases":"False"}
print c.update_dhcp_server(data)
pprint.pprint(c.get_dhcp_server())
data = {"name":"DHCP", "clientClass":"True", "clientClassLookupId":"openstack-client-class", "deleteOrphanedLeases":"True"}
# Set expressionConfigurationTraceLevel to 9 in the DHCPServer object to see more debugs in /var/nwreg2/local/logs/name_dhcp_1_log
# data = {"name":"DHCP", "clientClass":"True", "clientClassLookupId":"\"openstack-client-class\"", "deleteOrphanedLeases":"True", "expressionConfigurationTraceLevel":9}
data = {"name":"DHCP", "clientClass":"True", "clientClassLookupId":"\"openstack-client-class\"", "deleteOrphanedLeases":"True"}
print c.update_dhcp_server(data)
pprint.pprint(c.get_dhcp_server())
# Check _cpnr_reload_needed bool after updating DHCPServer
print "c._cpnr_reload_needed  = {0}".format(c._cpnr_reload_needed)

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

# Create policy object with name, optionList
test_name = "Create policy object with name, optionList"
print "\n======== {0} ========\n".format(test_name)
data = {"name":"policy1", "optionList":{"OptionItem":[{"number":"500","value":"00:09:3a:82"}]}}
print c.create_policy(data)
data = {"name":"policy2", "optionList":{"OptionItem":[{"number":"600","value":"00:09:3a:83"}]}}
print c.create_policy(data)
# Get all policies
pprint.pprint(c.get_policies())
# Check _cpnr_reload_needed bool after creating policy
print "c._cpnr_reload_needed  = {0}".format(c._cpnr_reload_needed)

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
# Check _cpnr_reload_needed bool after creating scope
print "c._cpnr_reload_needed  = {0}".format(c._cpnr_reload_needed)

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
data = {"name":"openstack-client-class", "clientLookupId":"(concat (request option 82 151) \"-\" (request chaddr))"}
print c.create_client_class(data)
# Get all ClientClasses
pprint.pprint(c.get_client_classes())
# Check _cpnr_reload_needed bool after creating client class
print "c._cpnr_reload_needed  = {0}".format(c._cpnr_reload_needed)

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
# Check _cpnr_reload_needed bool after creating VPN
print "c._cpnr_reload_needed  = {0}".format(c._cpnr_reload_needed)

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
data = {'clientClassName': 'openstack-client-class', 'embeddedPolicy': {'optionList':{'OptionItem':[{'number':'51','value':'00:09:3a:80'}]}}, 'hostName': 'host-name-1', 'name': '010203:04050607-1:2:3:4:5:6', 'reservedAddresses': [{'stringItem':'2.2.2.2'}]}
print c.create_client_entry(data)
data = {'clientClassName': 'openstack-client-class', 'embeddedPolicy': {'optionList':{'OptionItem':[{'number':'77','value':'00:09:4a:950'}]}}, 'hostName': 'host-name-2', 'name': '010203:04050608-11:22:33:44:55:66', 'reservedAddresses': [{'stringItem':'3.3.3.3'}]}
print c.create_client_entry(data)
# Get all ClientEntries
pprint.pprint(c.get_client_entries())

# Get a specific ClientEntry
test_name = "Get a specific ClientEntry"
print "\n======== {0} ========\n".format(test_name)
# Get 010203:04050607-1:2:3:4:5:6
ClientEntry = c.get_client_entry("010203:04050607-1:2:3:4:5:6")
pprint.pprint(ClientEntry)
# Get 010203:04050608-11:22:33:44:55:66
ClientEntry = c.get_client_entry("010203:04050608-11:22:33:44:55:66")
pprint.pprint(ClientEntry)

# Update policy
test_name = "Update policy"
print "\n======== {0} ========\n".format(test_name)
data = {"name":"policy1", "optionList":{"OptionItem":[{"number":"501","value":"00:09:3a:821"}]}}
pprint.pprint(c.get_policy("policy1"))
print c.update_policy("policy1", data)
# Verify if policy1 is updated correctly
pprint.pprint(c.get_policy("policy1"))
# Check _cpnr_reload_needed bool after updating policy
print "c._cpnr_reload_needed  = {0}".format(c._cpnr_reload_needed)

# Update client class
test_name = "Update client class"
print "\n======== {0} ========\n".format(test_name)
data = {"name":"openstack-client-class", "clientLookupId":"\"(request option 82 \"cisco-vpn-id1\")-(request chaddr)\""}
pprint.pprint(c.get_client_class("openstack-client-class"))
print c.update_client_class("openstack-client-class", data)
pprint.pprint(c.get_client_class("openstack-client-class"))
data = {"name":"openstack-client-class", "clientLookupId":"\"(request option 82 \"cisco-vpn-id\")-(request chaddr)\""}
data = {"name":"openstack-client-class", "clientLookupId":"(concat (request option 82 151) \"-\" (request chaddr))"}
print c.update_client_class("openstack-client-class", data)
pprint.pprint(c.get_client_class("openstack-client-class"))
# Check _cpnr_reload_needed bool after updating client class
print "c._cpnr_reload_needed  = {0}".format(c._cpnr_reload_needed)

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
# Check _cpnr_reload_needed bool after updating VPN
print "c._cpnr_reload_needed  = {0}".format(c._cpnr_reload_needed)

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
# Check _cpnr_reload_needed bool after updating scope
print "c._cpnr_reload_needed  = {0}".format(c._cpnr_reload_needed)

# Update client entry
test_name = "Update client entry"
print "\n======== {0} ========\n".format(test_name)
data = {'clientClassName': 'openstack-client-class', 'embeddedPolicy': {'optionList':{'OptionItem':[{'number':'7777','value':'00:09:4a:950'}]}}, 'hostName': 'host-name-2', 'name': '010203:04050608-11:22:33:44:55:66', 'reservedAddresses': [{'stringItem':'3.3.3.101'}]}
pprint.pprint(c.get_client_entry("010203:04050608-11:22:33:44:55:66"))
print c.update_client_entry("010203:04050608-11:22:33:44:55:66", data)
pprint.pprint(c.get_client_entry("010203:04050608-11:22:33:44:55:66"))
data = {'clientClassName': 'openstack-client-class', 'embeddedPolicy': {'optionList':{'OptionItem':[{'number':'77','value':'00:09:4a:950'}]}}, 'hostName': 'host-name-2', 'name': '010203:04050608-11:22:33:44:55:66', 'reservedAddresses': [{'stringItem':'3.3.3.3'}]}
print c.update_client_entry("010203:04050608-11:22:33:44:55:66", data)
pprint.pprint(c.get_client_entry("010203:04050608-11:22:33:44:55:66"))

# Reload CPNR server
test_name = "Reload CPNR server"
print "\n======== {0} ========\n".format(test_name)
print c.reload_cpnr_server()

# Get all leases
test_name = "Get all leases"
print "\n======== {0} ========\n".format(test_name)
Leases = c.get_leases()
pprint.pprint(Leases)

# sys.exit(0)

# Delete objects

# Delete policy
test_name = "Delete policy"
print "\n======== {0} ========\n".format(test_name)
# Delete policy1
print c.delete_policy("policy1")
# Delete policy2
print c.delete_policy("policy2")
# Check if policies are deleted correctly
pprint.pprint(c.get_policies())
# Check _cpnr_reload_needed bool after deleting policy
print "c._cpnr_reload_needed  = {0}".format(c._cpnr_reload_needed)

# Delete client class
test_name = "Delete client class"
print "\n======== {0} ========\n".format(test_name)
print (c.delete_client_class("openstack-client-class"))
# Check if client class is deleted correctly
pprint.pprint(c.get_client_classes())
# Check _cpnr_reload_needed bool after deleting client class
print "c._cpnr_reload_needed  = {0}".format(c._cpnr_reload_needed)

# Delete scope
test_name = "Delete scope"
print "\n======== {0} ========\n".format(test_name)
# Delete scope1
print c.delete_scope("scope1")
# Delete scope2
print c.delete_scope("scope2")
# Check if scopes are deleted correctly
pprint.pprint(c.get_scopes())
# Check _cpnr_reload_needed bool after deleting scope
print "c._cpnr_reload_needed  = {0}".format(c._cpnr_reload_needed)

# Delete client entry
test_name = "Delete client entry"
print "\n======== {0} ========\n".format(test_name)
# Delete 010203:04050607-1:2:3:4:5:6
print c.delete_client_entry("010203:04050607-1:2:3:4:5:6")
# Delete 010203:04050608-11:22:33:44:55:66
print c.delete_client_entry("010203:04050608-11:22:33:44:55:66")
# Check if client entries are deleted correctly
pprint.pprint(c.get_client_entries())

# Delete VPN
test_name = "Delete VPN"
print "\n======== {0} ========\n".format(test_name)
# Delete 418874ff-571b-46e2-a28a-75fe8afcb9e1
print c.delete_vpn("418874ff-571b-46e2-a28a-75fe8afcb9e1")
# Delete 418874ff-571b-46e2-a28a-75fe8afcb9e2
print c.delete_vpn("418874ff-571b-46e2-a28a-75fe8afcb9e2")
# Check if VPNs are deleted correctly
pprint.pprint(c.get_vpns())
# Check _cpnr_reload_needed bool after deleting VPN
print "c._cpnr_reload_needed  = {0}".format(c._cpnr_reload_needed)

# Update DHCPServer with defaults
test_name = "Update DHCPServer with defaults"
print "\n======== {0} ========\n".format(test_name)
data = {"name":"DHCP", "clientClass":"False", "clientClassLookupId":None, "deleteOrphanedLeases":"False"}
print c.update_dhcp_server(data)
pprint.pprint(c.get_dhcp_server())
# Check _cpnr_reload_needed bool after updating DHCPServer
print "c._cpnr_reload_needed  = {0}".format(c._cpnr_reload_needed)

print "\n================\n"

