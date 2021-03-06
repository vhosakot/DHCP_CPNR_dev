#!/usr/bin/env python

import sys
from neutron.plugins.cisco.cpnr import cpnr_client

scheme = "http"
ip = "172.29.68.140"
port = 8080
username = "cpnradmin"
password = "cpnradmin"
insecure = True

if len(sys.argv) == 2 and "." in sys.argv[1]:
    ip = sys.argv[1]

c = cpnr_client.CpnrClient(scheme, ip, port, username, password, insecure)

try:
    print c.get_version()
except Exception as e:
    print "ERROR : Exception raised by deleteall.py : ", e
    sys.exit(0)

while True:
    object_deleted = False
    for ce in c.get_client_entries():
       print 'Deleting ClientEntry: ' + ce['name']
       c.delete_client_entry(ce["name"])
       object_deleted = True
    for vpn in c.get_vpns():
       for scope in c.get_scopes(vpn["id"]):
          print 'Deleting Scope: ' + scope['name']
          c.delete_scope(scope["name"])
          object_deleted = True
       print 'Deleting VPN: ' + vpn['name']
       c.delete_vpn(vpn["name"])
       object_deleted = True
    
    for view in c.get_dns_views():
       if view['name'] == 'Default':
          continue
       viewid = view['viewId']
       for zone in c.get_ccm_zones(viewid=viewid):
          zoneid = zone['origin']
          for host in c.get_ccm_hosts(viewid=viewid, zoneid=zoneid):
              print 'Deleting CCMHost: ' + host['name']
              try: 
		  c.delete_ccm_host(host['name'], viewid=viewid, zoneid=zoneid)
              except Exception:
                  continue
              object_deleted = True
          print 'Deleting CCMZone: ' + zoneid
          c.delete_ccm_zone(zoneid, viewid=viewid)
          object_deleted = True
       for rz in c.get_ccm_reverse_zones(viewid=viewid):
          print 'Deleting CCMReverseZone: ' + rz['origin']
          c.delete_ccm_reverse_zone(rz['origin'], viewid=viewid)
          object_deleted = True
       print 'Deleting DnsView: ' + view['name']
       c.delete_dns_view(view['name'])
       object_deleted = True
    if object_deleted is False:
        # print "\n Done!\n" 
        break
