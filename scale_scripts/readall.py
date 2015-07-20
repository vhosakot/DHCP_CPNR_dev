#!/usr/bin/env python

import pprint 
from neutron.plugins.cisco.cpnr import cpnr_client

scheme = "http"
ip = "172.29.68.140"
port = 8080
username = "cpnradmin"
password = "cpnradmin"
insecure = True

c = cpnr_client.CpnrClient(scheme, ip, port, username, password, insecure)

print c.get_version()
for vpn in c.get_vpns():
   print "--VPN--"
   pprint.pprint(vpn)
   for scope in c.get_scopes(vpn["id"]):
      print "----SCOPE--"
      pprint.pprint(scope)
   for lease in c.get_leases(vpn["id"]):
      print "----LEASE--"
      pprint.pprint(lease)
for ce in c.get_client_entries():
   print "--CLIENT ENTRY--"
   pprint.pprint(ce)

for view in c.get_dns_views():
   if view['name'] == 'Default':
      continue
   print "VIEW"
   pprint.pprint(view)
   viewid = view['viewId']
   for zone in c.get_ccm_zones(viewid=viewid):
      print "ZONE"
      pprint.pprint(zone)
      zoneid = zone['origin']
      for host in c.get_ccm_hosts(viewid=viewid, zoneid=zoneid):
         print "HOST"
         pprint.pprint(host)
   for rz in c.get_ccm_reverse_zones(viewid=viewid):
      print "REVERSE ZONE"
      pprint.pprint(rz)

