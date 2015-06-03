#!/usr/bin/env python

import pprint 
from neutron.plugins.cisco.cpnr import cpnr_client

ip = "10.23.194.242"
port = 8080
username = "cpnradmin"
password = "cpnradmin"

c = cpnr_client.CpnrClient(ip, port, username, password)

print c.get_version()

while True:
    for ce in c.get_client_entries():
       print 'Deleting ClientEntry: ' + ce['name']
       c.delete_client_entry(ce["name"])
    for vpn in c.get_vpns():
       for scope in c.get_scopes(vpn["id"]):
          print 'Deleting Scope: ' + scope['name']
          c.delete_scope(scope["name"])
       print 'Deleting VPN: ' + vpn['name']
       c.delete_vpn(vpn["name"])
    
    for view in c.get_dns_views():
       if view['name'] == 'Default':
          continue
       viewid = view['viewId']
       for zone in c.get_ccm_zones(viewid=viewid):
          zoneid = zone['origin']
          for host in c.get_ccm_hosts(viewid=viewid, zoneid=zoneid):
              print 'Deleting CCMHost: ' + host['name']
              c.delete_ccm_host(host['name'], viewid=viewid, zoneid=zoneid)
          print 'Deleting CCMZone: ' + zoneid
          c.delete_ccm_zone(zoneid, viewid=viewid)
       for rz in c.get_ccm_reverse_zones(viewid=viewid):
          print 'Deleting CCMReverseZone: ' + rz['origin']
          c.delete_ccm_reverse_zone(rz['origin'], viewid=viewid)
       print 'Deleting DnsView: ' + view['name']
       c.delete_dns_view(view['name'])
