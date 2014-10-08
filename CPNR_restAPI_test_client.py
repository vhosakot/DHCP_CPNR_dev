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

print c
print CPNR_restApi(CPNRip, CPNRport, CPNRusername, CPNRpassword)
print dir(c)

# Check docstrings of all methods
print c.__doc__
print c.__init__.__doc__
print c.get_DHCPServer.__doc__
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

# Print all attributes
print "c.CPNR_server_ip       = {0}".format(c.CPNR_server_ip)
print "c.CPNR_server_port     = {0}".format(c.CPNR_server_port)
print "c.CPNR_server_username = {0}".format(c.CPNR_server_username)
print "c.auth                 = {0}".format(c.auth)
print "c.headers              = {0}".format(c.headers)
print "c.url                  = {0}".format(c.url)

# Get DHCPServer
DHCPServer = c.get_DHCPServer()
pprint.pprint(DHCPServer)

# Get all policies
Polices = c.get_policies()
pprint.pprint(Polices)

# Get a specific policy
policy1 = c.get_policy("system_default_policy")
pprint.pprint(policy1)
policy2 = c.get_policy("default")
pprint.pprint(policy2)

# Get all ClientClasses
ClientClasses = c.get_client_classes()
pprint.pprint(ClientClasses)

# Get a specific ClientClass
ClientClass = c.get_client_class()
pprint.pprint(ClientClass)

# Get all VPNs
VPNs = c.get_vpns()
pprint.pprint(VPNs)

# Get a specific VPN
VPN = c.get_vpn()
pprint.pprint(VPN)

# Get all scopes
Scopes = c.get_scopes()
pprint.pprint(Scopes)

# Get a specific scope
Scope = c.get_scope()
pprint.pprint(Scope)

# Get all ClientEntries
ClientEntries = c.get_client_entries()
pprint.pprint(ClientEntries)

# Get a specific ClientEntry
ClientEntry = c.get_client_entry()
pprint.pprint(ClientEntry)

# Create policy object with name, optionList
data = {"name":"policy1", "optionList":{"OptionItem":[{"number":"500","value":"00:09:3a:82"}]}}
print c.create_policy(data)
data = {"name":"policy2", "optionList":{"OptionItem":[{"number":"600","value":"00:09:3a:83"}]}}
print c.create_policy(data)
# Get all policies
pprint.pprint(c.get_policies())

# Create scope object with name, subnet, restrictToReservations, vpnId
data = {"name":"scope1", "subnet":"2.2.2.2/24", "restrictToReservations":"True", "vpnId":"30"}
print c.create_scope(data)
data = {"name":"scope2", "subnet":"3.3.3.3/24", "restrictToReservations":"True", "vpnId":"40"}
print c.create_scope(data)
# Get all scopes
pprint.pprint(c.get_scopes())

