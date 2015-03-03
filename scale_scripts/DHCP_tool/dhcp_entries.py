#! /usr/bin/env python

from argparse import ArgumentParser, RawTextHelpFormatter
import re
import uuid
import time
import subprocess
import sys
import os
import pdb
from neutronclient.v2_0 import client as nuclient

MAC_INT_LIST = []
IP_INT_LIST = []
PORT_ENTRIES = {}
IP_RANGES = []
creds = None
OS_USERNAME = None
OS_TENANT_NAME = None
OS_PASSWORD = None
OS_AUTH_URL = None
MAC_IP_NET_LIST = []

#Enable inserting of entries
EXECUTE = True

# Global debugging flags
ERROR = True
INFO = True
DEBUG = True

def Error(err_str):
    if ERROR == True:
        print time.ctime(time.time()) + ": ERROR: " + err_str

def Info(info_str):
    if INFO == True:
        print time.ctime(time.time()) + ": INFO: " + info_str

def Debug(debug_str):
    if DEBUG == True:
        print time.ctime(time.time()) + ": DEBUG: " + debug_str

'''
Read the OpenStack auth credentials.  If not set, check's to see if
they are set as environment variables.
'''
def get_keystone_creds():
    d = {}
    d['username'] = OS_USERNAME if OS_USERNAME != None else os.environ.get('OS_USERNAME', None)
    d['password'] = OS_PASSWORD if OS_PASSWORD != None else os.environ.get('OS_PASSWORD', None)
    d['auth_url'] = OS_AUTH_URL if OS_AUTH_URL != None else os.environ.get('OS_AUTH_URL', None)
    d['tenant_name'] = OS_TENANT_NAME if OS_TENANT_NAME != None else os.environ.get('OS_TENANT_NAME', None)

    if ((d['username'] == None) or
        (d['password'] == None) or
        (d['auth_url'] == None) or
        (d['tenant_name'] == None)):
        return None

    return d

def _validate_mac_addr(mac_addr):
    '''Validate mac address string to see if it is valid or not.
    '''
    try:
        tmp_obj = re.search(r'([0-9A-Fa-f]{2}[:]){5}([0-9A-Fa-f]{2})', mac_addr, re.I)
    except Exception as inst:
        raise TypeError("Invalid Mac Address: %s" % str(mac_addr))

    if (tmp_obj == None):
        raise TypeError("Invalid Mac Address: %s" % mac_addr)

    tmp_mac = tmp_obj.group()

    if tmp_mac != mac_addr:
        raise TypeError("Generated mac addr (%s) does not match argument mac addr (%s)" %
                        (tmp_mac, mac_addr))

def _validate_ip_addr(ip):
    try:
        tmp_obj = re.match(r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$", ip)
        #socket.inet_aton(ip)
    except Exception as Inst:
        raise TypeError("Invalid IP Address: %s" % str(ip))
    
    if (tmp_obj == None):
        raise TypeError("Invalid IP Address: %s" % str(ip))
    
    tmp_ip = tmp_obj.group()
    
    if tmp_ip != ip:
        raise TypeError("Generated IP addr (%s) does not match argument IP addr (%s)" %
                        (tmp_ip, ip))

def _convert_int_list_to_mac_str(int_list):
    return "%2.2x:%2.2x:%2.2x:%2.2x:%2.2x:%2.2x" % (int_list[0],
                                                    int_list[1],
                                                    int_list[2],
                                                    int_list[3],
                                                    int_list[4],
                                                    int_list[5])

def _convert_int_list_to_ip_str(int_list):
    return "%d.%d.%d.%d" % (int_list[0],
                            int_list[1],
                            int_list[2],
                            int_list[3])

def _convert_mac_str_to_int_list(start_mac):
    tmp_str_list = start_mac.split(":")
    tmp_int_list = []
    for tmp_str in tmp_str_list:
        tmp_int_list.append(int(tmp_str, 16))
    return tmp_int_list

def _convert_ip_str_to_int_list(start_ip):
    tmp_str_list = start_ip.split(".")
    tmp_int_list = []
    for tmp_str in tmp_str_list:
        tmp_int_list.append(int(tmp_str))
    return tmp_int_list

def _increment_byte(byte):
    if byte < 255:
        byte += 1
        return (False, byte)
    
    return (True, 0)

def _increment_mac():
    global MAC_INT_LIST

    i = 5
    while (i >= 0):
        increment_more, val = _increment_byte(MAC_INT_LIST[i])
        MAC_INT_LIST[i] = val
        if increment_more == False:
            break
        i -= 1

def _increment_ip():
    global IP_INT_LIST

    i = 3
    while (i >= 0):
        increment_more, val = _increment_byte(IP_INT_LIST[i])
        IP_INT_LIST[i] = val
        if increment_more == False:
            break
        i -= 1

'''
Looks up a network given its name using neutron API's
'''
def find_network(network_name):
    try:
        n = neutron.list_networks(fields=['id', 'tenant_id'], name=network_name)
    except Exception as inst:
        Error("Find Network: " + str(type(inst)) + " ARGS: " + str(inst.args))
        sys.exit(0)
    return n

'''
Looks up the subnets of network given its id using neutron API's
'''
def find_subnet(network_id):
    try:
        s = neutron.list_subnets(fields=['id', 'cidr'], network_id=network_id)
    except Exception as inst:
        Error("Find Subnet: " + str(type(inst)) + " ARGS: " + str(inst.args))
        sys.exit(0)
    return s

'''
Create a port entry in neutron using API's
'''
def create_port(mac_str, ip_str, network_id, subnet_id):
    Debug("INSERT PORT: MAC: %s IP: %s NETWORK: %s SUBNET: %s" % (mac_str, ip_str, network_id, subnet_id))

    if EXECUTE == False:
        return

    port_params = {}
    port_params['network_id'] = network_id
    port_params['admin_state_up'] = True
    port_params['mac_address'] = mac_str
    port_params['fixed_ips'] = [{'subnet_id': subnet_id, 'ip_address': ip_str}]
    
    port = {}
    port['port'] = port_params

    try:
        p = neutron.create_port(port)
    except Exception as inst:
        Debug("PORT: " + str(port))
        Error("Create Port: " + str(type(inst)) + " ARGS: " + str(inst.args))
        sys.exit(0)

'''
Delete a neutron port given its mac address
'''
def delete_port(mac_str, port_entries):
    port_id = port_entries.get(mac_str, None)

    if port_id != None:
        Debug("DELETE PORT: " + port_id)

        if EXECUTE == False:
            return

        try:
            neutron.delete_port(port_id)
        except Exception as inst:
            Error("Deleting Port: %s PORT: %s ARGS: %s" % (str(type(inst)), port_id, str(inst.args)))
            pass
    else:
        Error("Could not locate MAC: " + mac_str)

'''
Validate if the Start IP address is a valid IP and that the count
is an integer
'''
def validate_ip_range(ip_range):
    tmp_list = ip_range.split(":")
    _validate_ip_addr(tmp_list[0])
    tmp_int = int(tmp_list[1])
    if tmp_int <= 0:
        raise ValueError("Invalid value for count: %d(%s)" % (tmp_int, ip_range))
    return tmp_list

def validate_ip_ranges(ip_ranges, ip_range_list):
    tmp_list = ip_ranges.split("^")
    for tmp_range in tmp_list:
        ip_range = validate_ip_range(tmp_range)
        ip_range_list.append(ip_range)

'''
Read all the neutron port entries and create a mapping of their
mac address to their port ID.
'''
def read_port_entries(port_entries):
    try:
        p = neutron.list_ports()
    except Exception as inst:
        Error("List Ports: " + str(type(inst)) + " ARGS: " + str(inst.args))
        sys.exit(0)

    for port in p['ports']:
        port_entries[port['mac_address']] = port['id']

'''
Add port entries to neutron
'''
def insert_ip_range(ip_range_start, count, network_id, subnet_id):
    global IP_INT_LIST

    IP_INT_LIST = _convert_ip_str_to_int_list(ip_range_start)

    i = 0
    while i < int(ip_range[1]):
        mac_str = _convert_int_list_to_mac_str(MAC_INT_LIST)
        ip_str = _convert_int_list_to_ip_str(IP_INT_LIST)
        create_port(mac_str, ip_str, network_id, subnet_id)
        _increment_mac()
        _increment_ip()
        i += 1

'''
Delete port entries from neutron
'''
def delete_ip_range(ip_range_start, count, port_entries):
    global IP_INT_LIST

    IP_INT_LIST = _convert_ip_str_to_int_list(ip_range_start)

    i = 0
    while i < int(count):
        mac_str = _convert_int_list_to_mac_str(MAC_INT_LIST)
        ip_str = _convert_int_list_to_ip_str(IP_INT_LIST)
        delete_port(mac_str, port_entries)
        _increment_mac()
        _increment_ip()
        i += 1


if __name__ == "__main__":
    usage = 'dhcp_entries.py [-u OS_USERNAME] [-p OS_PASSWORD] [-U OS_AUTH_URL] \
[-T OS_TENANT_NAME] [-d] -m MAC_NET_IP_LIST'

    parser = ArgumentParser(description="Insert DHCP Entries Tool",
                            formatter_class=RawTextHelpFormatter,
                            usage=usage)
    parser.add_argument("-m", "--mac-net-ip-list", dest="mac_net_ip_list",
                        help='''\
List of MAC, Network & IP address ranges.  The format is:
MAC_NET_IP_LIST = START_MAC_1@IP_LIST_1@NETWORK_NAME_1[,START_MAC_1@IP_LIST_1@NETWORK_NAME_1]*
    Multiple entries are separated by ,
    MAC Address, IP_LIST & network are separated from each other by @
    For e.g.: de:ad:be:ef:00:01@40.1.1.10:10^40.1.0.10:10@int-net-1, (continued...)
              de:ad:be:ff:00:01@50.1.1.10:10^50.1.0.10:10@int-net-2
    In the example above, a total of 40 port entries will be created, 20 in
    int-net-1 and 20 in int-net-2
IP_LIST = START_IP_1:COUNT_1[^START_IP_2:COUNT_2]*
    Multiple entries are separated by ^
    For e.g.: 40.1.1.10:10 or 30.2.0.100:20^30.2.1.100:50
    40.1.1.10:10 - Insert 10 ip addresses starting with 40.1.1.10
    30.2.0.100:20^30.2.1.100:50 - Insert 20 ip addresses starting
                                  with 30.2.0.100 and then insert
                                  another 50 addresses starting
                                  with 30.2.1.100
                        ''', action="store")
    parser.add_argument("-u", "--os-username", dest="user",
                        help="User name to use for Access",
                        action="store", default=None)
    parser.add_argument("-p", "--os-password", dest="passwd",
                        help="Password of user to use for Access",
                        action="store", default=None)
    parser.add_argument("-U", "--os-auth-url", dest="auth_url",
                        help="Keystone Auth URL",
                        action="store", default=None)
    parser.add_argument("-T", "--os-tenant-name", dest="tenant_name",
                        help="Tenant Name",
                        action="store", default=None)
    parser.add_argument("-d", "--delete", dest="delete",
                        help="Delete DHCP entries, Default is to insert entries",
                        action="store_true", default=False)
    parser.add_argument("-D", "--debug", dest="debug",
                        help="Enable debugging, Default: False",
                        action="store_true", default=False)
    
    options = parser.parse_args()
    DEBUG = options.debug

    if (options.mac_net_ip_list == None):
        raise RuntimeError("Start mac, ip, network list not provided")

    '''
    if (options.ip_list == None):
        raise RuntimeError("Start IP address not provided")

    if (options.network == None):
        raise RuntimeError("OpenStack network name not provided")
    '''

    if (options.user != None):
        OS_USERNAME = options.user

    if (options.passwd != None):
        OS_PASSWORD = options.passwd

    if (options.tenant_name != None):
        OS_TENANT_NAME = options.tenant_name

    if (options.auth_url != None):
        OS_AUTH_URL = options.auth_url

    creds = get_keystone_creds()
    if creds == None:
        raise RunTimeError("Could not find Keystone environment variables")
    neutron = nuclient.Client(**creds)

    tmp_nets = options.mac_net_ip_list.split(",")
    for net in tmp_nets:
        tmp_mac_ip_net = net.split("@")
        mac = tmp_mac_ip_net[0]
        ip_list = tmp_mac_ip_net[1]
        network_name = tmp_mac_ip_net[2]
        _validate_mac_addr(mac)
        ip_range_list = []
        validate_ip_ranges(ip_list, ip_range_list)
        tmp_network = find_network(network_name)
        if tmp_network == None:
            raise RuntimeError("Could not locate Network: " + network_name)
        MAC_IP_NET_LIST.append((mac, ip_range_list, tmp_network, network_name))

    if options.delete == True:
        read_port_entries(PORT_ENTRIES)

        for mac_ip_net in MAC_IP_NET_LIST:
            mac = mac_ip_net[0]
            ip_list = mac_ip_net[1]
            network = mac_ip_net[2]
            network_name = mac_ip_net[3]
            tenant_id = network['networks'][0]['tenant_id']
            network_id = network['networks'][0]['id']
            MAC_INT_LIST = _convert_mac_str_to_int_list(mac)

            for ip_range in ip_list:
                delete_ip_range(ip_range[0], int(ip_range[1]), PORT_ENTRIES)
    else:
        for mac_ip_net in MAC_IP_NET_LIST:
            mac = mac_ip_net[0]
            ip_list = mac_ip_net[1]
            network = mac_ip_net[2]
            network_name = mac_ip_net[3]
            tenant_id = network['networks'][0]['tenant_id']
            network_id = network['networks'][0]['id']
            subnet = find_subnet(network_id)
            if subnet != None:
                # Maybe add validation that start address and end address are part
                # of the subnet
                subnet_id = subnet['subnets'][0]['id']
                Debug("Found Subnet: %s" % (subnet['subnets'][0]['cidr']))
                MAC_INT_LIST = _convert_mac_str_to_int_list(mac)

                for ip_range in ip_list:
                    insert_ip_range(ip_range[0], int(ip_range[1]), network_id, subnet_id)
            else:
                Error("Could not locate subnet for network: '%s'" % (network_name))

