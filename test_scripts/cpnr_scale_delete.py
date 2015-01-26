#! /usr/bin/python

# Run the command below to delete the objects created by
# cpnr_scale.py or cpnr_scale_multi_threaded.py
# ./cpnr_scale_delete.py

import sys
import pprint
import logging
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

# Delete scope objects
test_name = "Delete scope objects"
print "\n======== {0} ========\n".format(test_name)
while c.get_scopes() != []:
    for scope in c.get_scopes():
        print "{0}, return code = {1}".format(scope['name'], c.delete_scope(scope['name']))

# Get all scopes
pprint.pprint(c.get_scopes())

if c.get_client_classes() != []:
    # Delete client class
    test_name = "Delete client class" 
    print "\n======== {0} ========\n".format(test_name)
    print (c.delete_client_class("openstack-client-class"))
    # Check if client class is deleted correctly
    pprint.pprint(c.get_client_classes())

# Delete client entry objects
test_name = "Delete client entry objects"
print "\n======== {0} ========\n".format(test_name)
while c.get_client_entries() != []:
    for ce in c.get_client_entries():
        print "name = {0}, return code = {1}".format(ce['name'], c.delete_client_entry(ce['name']))

# Get all ClientEntries
pprint.pprint(c.get_client_entries())

# Delete VPNs
test_name = "Delete VPNs"
print "\n======== {0} ========\n".format(test_name)
while c.get_vpns() != []:
    for vpn in c.get_vpns():
        print "vpn id {0}, return code = {1}".format(vpn['id'], c.delete_vpn(vpn['name']))

# Get all scopes
pprint.pprint(c.get_scopes())

# Get all ClientEntries
pprint.pprint(c.get_client_entries())

# Get all VPNs
pprint.pprint(c.get_vpns())
