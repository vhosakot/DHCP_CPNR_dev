#! /usr/bin/python

########
# Test client to unit-test CPNR_restAPI.py
########

import pprint
from CPNR_restAPI import CPNR_restApi

CPNRip = "192.168.122.247"
CPNRport = 8080
CPNRusername = "cpnradmin"
CPNRpassword = "password"

c = CPNR_restApi(CPNRip, CPNRport, CPNRusername, CPNRpassword)

print c
print CPNR_restApi(CPNRip, CPNRport, CPNRusername, CPNRpassword)
print dir(c)

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

print "c.CPNR_server_ip       = {0}".format(c.CPNR_server_ip)
print "c.CPNR_server_port     = {0}".format(c.CPNR_server_port)
print "c.CPNR_server_username = {0}".format(c.CPNR_server_username)
print "c.auth                 = {0}".format(c.auth)
print "c.headers              = {0}".format(c.headers)
print "c.url                  = {0}".format(c.url)

DHCPServer = c.get_DHCPServer()
pprint.pprint(DHCPServer)

Polices = c.get_policies()
pprint.pprint(Polices)

policy1 = c.get_policy("system_default_policy")
pprint.pprint(policy1)
policy2 = c.get_policy("default")
pprint.pprint(policy2)

ClientClasses = c.get_client_classes()
pprint.pprint(ClientClasses)

ClientClass = c.get_client_class()
pprint.pprint(ClientClass)

VPNs = c.get_vpns()
pprint.pprint(VPNs)

VPN = c.get_vpn()
pprint.pprint(VPN)

Scopes = c.get_scopes()
pprint.pprint(Scopes)

Scope = c.get_scope()
pprint.pprint(Scope)

ClientEntries = c.get_client_entries()
pprint.pprint(ClientEntries)

ClientEntry = c.get_client_entry()
pprint.pprint(ClientEntry)

# Create policy object with name, optionList
data = {"name":"policy1", "optionList":{"OptionItem":[{"number":"500","value":"00:09:3a:82"}]}}
print c.create_policy(data)
data = {"name":"policy2", "optionList":{"OptionItem":[{"number":"600","value":"00:09:3a:83"}]}}
print c.create_policy(data)
pprint.pprint(c.get_policies())

# Create scope object with name, subnet, restrictToReservations, vpnId
data = {"name":"scope1", "subnet":"2.2.2.2/24", "restrictToReservations":"True", "vpnId":"30"}
print c.create_scope(data)
data = {"name":"scope2", "subnet":"3.3.3.3/24", "restrictToReservations":"True", "vpnId":"40"}
print c.create_scope(data)
pprint.pprint(c.get_scopes())

