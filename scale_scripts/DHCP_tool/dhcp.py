#! /usr/bin/env python

# Set log level to benefit from Scapy warnings
import logging
logging.getLogger("scapy").setLevel(logging.ERROR)
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

from scapy.all import *
from argparse import ArgumentParser, RawTextHelpFormatter
import re
import sys
import subprocess
import pdb
import time
import threading
import datetime
import sys
import os
from tabulate import tabulate
import json
import socket
from Queue import Queue

conf.sniff_promisc = True
conf.use_pcap = True
import scapy.arch.pcapdnet

# Global variables
global_socket = ""
global_pkt = ""
q = Queue(maxsize=0)
dhcp_tool = None
DEFAULT_SNAME = ''
DEFAULT_FILE = ''

# Added by Vikram
# Initial retry time per section 4.1 in RFC 2131 
# https://tools.ietf.org/html/rfc2131#section-4.1
RETRY_IN_SECS = 4

MS_PER_SEC = 1000
SLEEP_MS = 50 # Sleep for 50 milli seconds
SLEEP_SEC = float(SLEEP_MS) / MS_PER_SEC
RETRY_SLEEP_COUNT = (RETRY_IN_SECS * MS_PER_SEC) / SLEEP_MS

# dhcp messages
DHCPDISCOVER = 1
DHCPOFFER = 2
DHCPREQUEST = 3
DHCPDECLINE = 4
DHCPACK = 5
DHCPNACK = 6
DHCPRELEASE = 7
DHCPINFORM = 8

# Test Mapping
TEST_IP = None
TEST_MAC = None

# Global debugging flags
ERROR = True
INFO = True
DEBUG = False

def Error(err_str):
    if ERROR == True:
        print str(datetime.datetime.now()).split()[1] + ": ERROR: " + err_str

def Info(info_str):
    if INFO == True:
        print str(datetime.datetime.now()).split()[1] + ": INFO: " + info_str

def Debug(debug_str):
    if DEBUG == True:
        print str(datetime.datetime.now()).split()[1] + ": DEBUG: " + debug_str

def calculate_time_diff(ts1, ts2):
    '''Calculate the difference between two timestamps.
    ts2 should be 'None' or if not 'None', then it should
    be greater than ts1.
    '''
    #print "ts1 = {0}".format(ts1)
    #print "ts2 = {0}".format(ts2)
    if ts2 == None:
        return None
    else:
        return ts2 - ts1

'''DHCP Client class.  One instance of this class is created
for each mac address that we are simulating.
'''
class DHCPClient():
    def __init__(self, mac_addr, xid, host_count, client_RETRY_IN_SECS):
        self.mac_addr = mac_addr
        self.xid = xid
        self.host_count = host_count
        self.ip = None
        self.server_ip = None
        self.discover_sent = False

        # Added by Vikram
        # https://tools.ietf.org/html/rfc2131#section-4.1
        self.client_RETRY_IN_SECS = client_RETRY_IN_SECS + random.uniform(-1, 1)

        self.offer_received = False
        self.request_sent = False
        self.acked = False
        self.discover_sent_count = 0
        self.offer_received_count = 0
        self.request_sent_count = 0
        self.acked_count = 0
        self.arp_count = 0
        self.icmp_count = 0
        self.discover_sent_ts = None
        self.first_discover_sent_ts = None
        self.offer_received_ts = None
        self.request_sent_ts = None
        self.first_request_sent_ts = None
        self.acked_ts = None
        self.retry_tick_count = 0
    
    '''
    Set the IP that was received for this DHCP Client instance
    '''
    def set_ip(self, ip):
        self.ip = ip

    '''
    Set the IP address of the server that responded to us
    '''
    def set_server_ip(self, server_ip):
        self.server_ip = server_ip

    '''
    Convert the clients' mac address into a character byte string
    '''
    def get_chaddr(self):
        chaddr = ''
        tmp_list = self.mac_addr.split(':')
        for tmp in tmp_list:
            chaddr += chr(int(tmp, 16))
        i = 6
        while i < 16:
            chaddr += chr(0)
            i += 1
        return chaddr

    '''
    Convert an integer list into a character list string
    '''
    def get_param_req_list(self, int_list):
        req_list = ''
        for param in int_list:
            req_list += chr(param)
        return req_list

    '''
    Get a character string representation of all the parameters
    we are interested in for a DHCP Discover message
    '''
    def get_discover_param_req_list(self):
        param_int_list = [ 1, 28, 2, 3, 15, 6, 119, 12, 44, 47, 26, 121, 42 ]
        return self.get_param_req_list(param_int_list)

    '''
    Prepare a skeleton BOOTP packet instance
    '''
    @classmethod
    def prepare_bootp_pkt(cls):
        global global_pkt
        global_pkt = Ether()/IP()/UDP()/BOOTP()

        # Setup Ethernet Header
        ether_layer = global_pkt[Ether]
        ether_layer.dst = "ff:ff:ff:ff:ff:ff"

        # Setup IP Header
        ip_layer = global_pkt[IP]
        ip_layer.ihl = 5 # length
        ip_layer.src = "0.0.0.0"
        ip_layer.dst = "255.255.255.255"
        ip_layer.len = 328

        # Setup UDP Header
        udp_layer = global_pkt[UDP]
        udp_layer.sport = 68
        udp_layer.dport = 67
        udp_layer.len = 308

        # Setup BOOTP Header
        bootp_layer = global_pkt[BOOTP]
        bootp_layer.sname = DEFAULT_SNAME
        bootp_layer.file = DEFAULT_FILE

        return global_pkt
        
    '''
    Send a DHCP Discover message
    '''
    def send_discover(self, interface, retry):
        global global_pkt

        pkt = global_pkt
        ether_layer = pkt[Ether]
        ether_layer.src = self.mac_addr

        bootp_layer = pkt[BOOTP]
        bootp_layer.xid = self.xid
        bootp_layer.chaddr = self.get_chaddr()

        # Setup DHCP Options
        dhcp_options = [("message-type", "discover"),
                        ("hostname", "ubuntu-server-%d" % self.host_count),
                        ("param_req_list", self.get_discover_param_req_list()),
                        "end"
                        ]
        
        tmp_dhcp = DHCP(options=dhcp_options)

        # Send DISCOVER
        pad = Padding()
        pad.load = '\x00' * 24
        pkt = pkt/tmp_dhcp/pad
        #ip_layer = pkt[IP]
        #udp_layer = pkt[UDP]
        #sendp(pkt, iface=interface, verbose=0)
        global_socket.send(pkt)
        self.discover_sent_ts = datetime.datetime.now()
        self.discover_sent = True
        Debug("%s DHCPDISCOVER: %s" % ("Sending" if retry == False else ("Retrying (after " + str(self.client_RETRY_IN_SECS) + " s)"), self.mac_addr))
        self.discover_sent_count +=1
        
    
    '''
    Send a DHCP Request message
    '''
    def send_request(self, interface, retry):
        global global_pkt

        pkt = global_pkt
        ether_layer = pkt[Ether]
        ether_layer.src = self.mac_addr

        bootp_layer = pkt[BOOTP]
        bootp_layer.xid = self.xid
        bootp_layer.chaddr = self.get_chaddr()

        # Setup DHCP Options
        dhcp_options = [("message-type", "request"),
                        ("server_id", self.server_ip),
                        ("requested_addr", self.ip),
                        ("hostname", "ubuntu-server-%d" % self.host_count),
                        ("param_req_list", self.get_discover_param_req_list()),
                        "end"
                        ]
        
        tmp_dhcp = DHCP(options=dhcp_options)

        bootp_layer = pkt[BOOTP]
        bootp_layer.yiaddr = self.ip
        bootp_layer.siaddr = self.server_ip

        # Send DHCPREQUEST
        pad = Padding()
        pad.load = '\x00' * 24
        pkt = pkt/tmp_dhcp/pad
        #ip_layer = pkt[IP]
        #udp_layer = pkt[UDP]
        #sendp(pkt, iface=interface, verbose=0)
        global_socket.send(pkt)
        self.request_sent_ts = datetime.datetime.now()
        self.request_sent = True
        if self.first_request_sent_ts == None:
            self.first_request_sent_ts = self.request_sent_ts
        self.request_sent_count +=1
        Debug("%s DHCPREQUEST: %s" % ("Sending" if retry == False else ("Retrying (after " + str(self.client_RETRY_IN_SECS) + " s)"), self.mac_addr))


    '''
    Figure out the state of this DHCP Client and send the appropriate packet
    '''
    def send_state_pkt(self, interface):
        if (self.acked == True):
            # Nothing to do...
            #Debug("Skipping %s b/c 4-way is already complete" % (self.mac_addr))
            return False
        elif ((self.discover_sent == False) or
              ((self.discover_sent == True) and 
               (self.offer_received == False))):
            '''
            Send a DHCP Discover if we have not sent one, or if we have
            sent one but not yet received an Offer yet and the self.client_RETRY_IN_SECS
            number of seconds have elapsed
            '''
            if self.discover_sent == True:
                '''
                If Discover was sent, but no Offer was received, then
                Check to see if RETRY_IN_SECS number of seconds has elapsed.
                If so then resend a Discover for this mac address
                '''
                cur_time = datetime.datetime.now()
                time_diff = calculate_time_diff(self.discover_sent_ts, cur_time)
                if self.client_RETRY_IN_SECS > 64:
                    self.client_RETRY_IN_SECS = RETRY_IN_SECS + random.uniform(-1, 1)
                if time_diff.total_seconds() > self.client_RETRY_IN_SECS:
                    # Added by Vikram
                    if self.offer_received == False:
                        self.send_discover(interface, True)
                        # Retry backoff algo:
                        # Double the retry time and add by a random number between -1 and 1
                        self.client_RETRY_IN_SECS = (self.client_RETRY_IN_SECS * 2) + random.uniform(-1, 1)
            else:
                self.send_discover(interface, False)
                if self.first_discover_sent_ts == None:
                    self.first_discover_sent_ts = datetime.datetime.now()
            return True
        elif ((self.request_sent == False) or
              ((self.request_sent == True) and 
               (self.acked == False))):
            '''
            Send a DHCP Request if we have not sent one, or if we have
            sent one but not yet received an Ack yet and self.client_RETRY_IN_SECS
            number of seconds have elapsed
            '''
            if self.request_sent == True:
                '''
                If Request was sent, but no Ack was received, then
                Check to see if RETRY_IN_SECS number of seconds has elapsed.
                If so then resend a Request for this mac address.
                '''
                cur_time = datetime.datetime.now()
                time_diff = calculate_time_diff(self.request_sent_ts, cur_time)
                if self.client_RETRY_IN_SECS > 64:
                    self.client_RETRY_IN_SECS = RETRY_IN_SECS + random.uniform(-1, 1)
                if time_diff.total_seconds() > self.client_RETRY_IN_SECS:
                    # Added by Vikram
                    if self.acked == False:
                        self.send_request(interface, True)
                        # Retry backoff algo:
                        # Double the retry time and add by a random number between -1 and 1
                        self.client_RETRY_IN_SECS = (self.client_RETRY_IN_SECS * 2) + random.uniform(-1, 1)
            else:
                self.send_request(interface, False)
                if self.first_request_sent_ts == None:
                    self.first_request_sent_ts = datetime.datetime.now()
            return True
        else:
            state_str = ''
            state_str += 'T ' if self.discover_sent == True else 'F '
            state_str += 'T ' if self.offer_received == True else 'F '
            state_str += 'T ' if self.request_sent == True else 'F '
            state_str += 'T ' if self.acked == True else 'F '
            Error("Could not figure out which packet to send: MAC: %s STATE: %s" % (self.mac_addr, state_str))
        return False

    '''
    Calculate the time difference for how long it took to get an offer
    '''
    def calculate_discover_difference(self):
        return calculate_time_diff(self.first_discover_sent_ts,
                                   self.offer_received_ts)
    '''
    Calculate the time difference for how long it took to get an ack
    '''
    def calculate_request_difference(self):
        #print "\nfirst_request_sent_ts = {0}".format(self.first_request_sent_ts)
        #print "acked_ts        = {0}".format(self.acked_ts)
        return calculate_time_diff(self.first_request_sent_ts,
                                   self.acked_ts)

class DHCPTool():
    '''The DHCP Tool object.  This takes a starting MAC address
    and a count of how many clients to simulate.  It can then
    print an output status of how many clients got processed.
    '''
    def __init__(self, start_mac, interface, count, test, rate):
        if test == None:
            self._validate_mac_addr(start_mac)
            self._start_mac_addr = start_mac.lower()
            self._cur_mac = self._start_mac_addr
        self.interface = interface
        self.clients = {}
        self.ip = {}
        self.total_acked = 0
        self.total_disc_diff = None
        self.total_request_diff = None
        try:
            self.count = int(count)

            if self.count <= 0:
                raise ValueError("Invalid value for count: %d" % (self.count))
        except ValueError:
            raise ValueError("Invalid value for count: %s" % (count))

        try:
            self.rate = int(rate)

            if self.rate <= 0:
                raise ValueError("Invalid value for rate: %d" % (self.rate))
        except ValueError:
            raise ValueError("Invalid value for rate: %s" % (rate))

    '''
    Convert a MAC in string form to an integer list
    '''
    def _convert_mac_str_to_int_list(self, start_mac):
        tmp_str_list = start_mac.split(":")
        tmp_int_list = []
        for tmp_str in tmp_str_list:
            tmp_int_list.append(int(tmp_str, 16))
        return tmp_int_list

    '''
    Convert an integer list to a MAC string
    '''
    def _convert_int_list_to_mac_str(self, int_list):
        return "%2.2x:%2.2x:%2.2x:%2.2x:%2.2x:%2.2x" % (int_list[0],
                                                        int_list[1],
                                                        int_list[2],
                                                        int_list[3],
                                                        int_list[4],
                                                        int_list[5])

    
    def add_to_diff(self, discover, time_diff):
        '''Add the time difference to the total time difference.
        Avg is calculated at the end by dividing the total time
        difference by the number of received packets.
        '''
        if discover == True:
            if self.total_disc_diff == None:
                self.total_disc_diff = time_diff
            else:
                self.total_disc_diff += time_diff
        else:
            if self.total_request_diff == None:
                self.total_request_diff = time_diff
            else:
                self.total_request_diff += time_diff

    def _increment_mac(self, n):
        mac_split = self._cur_mac.split(":")
        prefix = mac_split[0] + mac_split[1]
        part_mac = "{:08X}".format(int("1", 16) + (n-1))
        m = prefix + part_mac
        self._cur_mac = ':'.join(a+b for a,b in zip(m[::2], m[1::2]))
        self._cur_mac = self._cur_mac.lower()

    def _validate_mac_addr(self, mac_addr):
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

    def _validate_ip_addr(self, ip):
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

    def convert_chaddr_to_mac(self, chaddr):
        tmp_mac = ''
        i = 0
        while i < 6:
            tmp_mac += "%2.2x:" % ord(chaddr[i])
            i += 1

        # Drop the last ':'
        return tmp_mac[:-1]

    def get_dhcp_client(self, chaddr):
        '''Convert the characters into a MAC string and lookup the
        DHCP Client object and return it
        '''
        mac = self.convert_chaddr_to_mac(chaddr)
        return mac, self.clients.get(mac, None)

    def add_ip_mapping(self, ip, mac):
        '''Add a mapping from the IP to the MAC Address
        '''
        self.ip[ip] = mac

    def get_ip_mapping(self, ip):
        '''Lookup the MAC address for a given IP
        '''
        return self.ip.get(ip, None)

    def start_reply_thread(self):
        '''Start a thread for processing incoming replies and other packets like
        ICMP echo requests and ARP Queries
        '''
        # Start a thread to handle responses of requests that are sent
        t = threading.Thread(target = handle_replies_thread, args = (dhcp_tool,))
        t.daemon = True
        t.start()

    def generate_output(self):
        '''Show details of packets sent and received.
        '''
        rows = []

        total_discover_sent = 0
        total_offer_received = 0
        total_request_sent = 0
        total_acked = 0
        total_arp_count = 0
        total_icmp_count = 0

        for mac in sorted(self.clients):
            d = self.clients[mac]
            row = [mac]

            row.append(str(d.discover_sent_count))
            total_discover_sent += d.discover_sent_count

            row.append(str(d.offer_received_count))
            total_offer_received += d.offer_received_count

            row.append(str(d.request_sent_count))
            total_request_sent += d.request_sent_count

            row.append(str(d.acked_count))
            total_acked += d.acked_count

            row.append(d.ip)

            row.append(str(d.arp_count))
            total_arp_count += d.arp_count

            row.append(str(d.icmp_count))
            total_icmp_count += d.icmp_count

            tmp_diff = d.calculate_discover_difference()
            if tmp_diff != None:
                row.append(tmp_diff.total_seconds())
                self.add_to_diff(True, tmp_diff)

            tmp_diff = d.calculate_request_difference()
            if tmp_diff != None:
                #print "one = {0}".format(tmp_diff)
                row.append(tmp_diff.total_seconds())
                #print "two = {0}".format(tmp_diff.total_seconds())
                self.add_to_diff(False, tmp_diff)

            rows.append(row)

        if options.details == True:
            headers = ['MAC', 'Discover Sent', 'Offer Received', 'Request Sent', 'Ack Received', 'IP Address', 'ARP Count', 'ICMP Count', 'Offer Delay', 'Ack Delay']
            print tabulate(rows, headers = headers)

        headers = ['Discover Sent', 'Offer Received', 'Request Sent', 'Ack Received', 'ARP Count', 'ICMP Count', 'Avg Offer Delay', 'Avg Ack Delay']
        row = [[str(total_discover_sent),
               str(total_offer_received),
               str(total_request_sent),
               str(total_acked),
               str(total_arp_count),
               str(total_icmp_count),
               'None' if self.total_disc_diff == None else str((self.total_disc_diff.total_seconds() / len(rows))),
               'None' if self.total_request_diff == None else str((self.total_request_diff.total_seconds() / len(rows)))]]

        print tabulate(row, headers = headers)

    '''
    Create an instance of the DHCPClient class for the
    given mac address
    '''
    def create_dhcp_client(self, mac, xid, count):
        d = self.clients.get(mac, None)
        if d == None:
            d = DHCPClient(mac, xid, count, RETRY_IN_SECS)
            self.clients[mac] = d
        return d

    '''
    Loop through all the DHCP clients and send the appropriate packet
    for each one of them (if needed)
    '''
    def loop_dhcp(self):
        # Loop to send DHCP packets.
        first = True
        tmp_count = 0
        pkt_sent = False
        self._cur_mac = self._start_mac_addr
        while tmp_count < self.count:
            tmp_rate = 0
            #time.sleep(SLEEP_SEC)
            #print "here1"
            if first == True:
                first = False
                continue
            while tmp_rate < self.rate:
                tmp_mac = self._cur_mac
                d = self.create_dhcp_client(tmp_mac, 556223005 + tmp_count, tmp_count)
                if d.send_state_pkt(self.interface):
                    pkt_sent = True
                tmp_rate += 1
                tmp_count += 1
                self._increment_mac(tmp_count)
        return pkt_sent

    def start(self, iface):
        '''Start sending the DHCP requests and processing the DHCP responses
        '''
        # Added by Vikram
        global global_socket
        global global_pkt

        try:
            # Create one global L2 socket
            print "\nCreating L2socket for {0}\n".format(iface)
            global_socket = conf.L2socket(iface=iface)
        except Exception as inst:
            print "\n An exception occurred when L2socket was created for {0}".format(iface)
            print " global_socket = {0}\n".format(global_socket)
            print type(inst)
            print inst.args
            print inst

        # Prepare the global skeleton bootp packet
        global_pkt = DHCPClient.prepare_bootp_pkt()

        # Start 500 threads to get replies from Q
        for i in range(0, 500):
            t = threading.Thread(target = get_replies_from_Q)
            t.daemon = True
            t.start()

        time.sleep(3)

        # Start thread to put replies into Q
        self.start_reply_thread()
        time.sleep(0.5)
        #print "here2"
       
        pkt_sent = self.loop_dhcp()
        while pkt_sent == True:
            #time.sleep(SLEEP_SEC)
            #print "here3"
            pkt_sent = self.loop_dhcp()

        Debug("Acked all %s clients" % self.count)

        if options.keepalive == True:
            Debug("Keeping process alive...")
            while True:
                time.sleep(SLEEP_SEC)
                print "here4"

        self.generate_output()
        return
                
def start_capture(cap_filter, iface, handle_pkt_func):
    '''Routine to start sniffing for packets.  This is used
    by the DHCP tool in to receive DHCP responses and process
    them.
    '''
    sniff(iface=iface, filter=cap_filter, 
          store=0, prn=handle_pkt_func)
        
def get_message_type(opts):
    # opt is a tuple like: (opt_type, value)
    for opt in opts:
        if opt[0] == 'message-type':
            return opt[1]
    return 0

def handle_replies(pkt):
    '''DHCP response handler.  It receives responses
    and correlates them to requests that have been sent earlier.
    It also replies to ICMP echo requests and ARP queries for
    known IP and MAC addresses
    '''
    global dhcp_tool

    if DHCP in pkt:
        bootp_layer = pkt[BOOTP]
        if bootp_layer.op == 2:
            mac, client = dhcp_tool.get_dhcp_client(bootp_layer.chaddr)
            msg_type = get_message_type(pkt[DHCP].options)

            # Added by Vikram
            # print pkt[IP].src
            # print pkt[IP].dst
            # print pkt[DHCP].options

            if client != None:
                if msg_type == DHCPOFFER and client.acked == False:
                    Debug("Received DHCPOFFER: " + mac)
                    client.offer_received_ts = datetime.datetime.now()
                    client.set_ip(bootp_layer.yiaddr)
                    client.set_server_ip(bootp_layer.siaddr)
                    dhcp_tool.add_ip_mapping(bootp_layer.yiaddr, mac)
                    if client.acked == False:
                        client.send_request(options.interface, False)
                    client.offer_received = True
                    client.offer_received_count += 1
                elif msg_type == DHCPACK:
                    client.acked_ts = datetime.datetime.now()
                    client.acked = True
                    Debug("Received DHCPACK: " + mac)
                    client.acked_count += 1
                    dhcp_tool.total_acked += 1
                elif msg_type == DHCPOFFER:
                    Debug("Received duplicate DHCPOFFER: " + mac)
                elif msg_type == DHCPNACK:
                    Error("Received DHCPNACK: " + mac)
                else:
                    Error("Received unknown DHCP packet: " + mac + ", msg_type = " + msg_type)
            else:
                Error("Received DHCP message for unknown mac: %s" % mac)

packet_count_put_into_Q = 0

def put_replies_into_Q(pkt):
    global q
    global packet_count_put_into_Q
    if DHCP in pkt and pkt[BOOTP].op == 2:
        q.put(pkt)
        packet_count_put_into_Q = packet_count_put_into_Q + 1

def get_replies_from_Q():
    global q
    while True:
        print "\n Q size = {0}".format(q.qsize())
        reply = q.get()
        handle_replies(reply)

def handle_replies_thread(dhcp_tool):
    '''Routine use by the DHCP tool to start a new thread for 
    processing incoming DHCP/ARP/ICMP packets.
    '''
    Debug("Starting replies handler...")
    #start_capture("", options.interface, handle_replies)
    start_capture("", options.interface, put_replies_into_Q)

if __name__ == "__main__":
    usage = 'dhcp.py -m START_MAC_ADDR -i INTERFACE [-k] [-c COUNT] [-D DETAILS] [-R RATE] [-d] [-e]'

    parser = ArgumentParser(description="DHCP Tool",
                            formatter_class=RawTextHelpFormatter,
                            usage=usage)
    parser.add_argument("-D", "--show-details", dest="details",
                        help="Show details of each mac address in a tabular format, Default: False",
                        action="store_true", default=False)
    parser.add_argument("-d", "--debug", dest="debug",
                        help="Enable debugging, Default: False",
                        action="store_true", default=False)
    parser.add_argument("-e", "--disable-error", dest="error",
                        help="Disable printing of errors, Default: True",
                        action="store_false", default=True)
    parser.add_argument("-i", "--interface", dest="interface",
                        help="Interface for sending/receiving packets",
                        action="store")
    parser.add_argument("-m", "--start-mac", dest="start_mac_addr",
                        help="Starting mac address for DHCP clients",
                        action="store")
    parser.add_argument("-c", "--count", dest="count",
                        help="Number of DHCP clients to simulate, Default: 1",
                        action="store", default="1")
    parser.add_argument("-R", "--rate", dest="rate",
                        help="Number of DHCP requests to send per second, Default: 1",
                        action="store", default="1")
    parser.add_argument("-t", "--test", dest="test",
                        help="Test IP/MAC mapping to try ARP response and ICMP response",
                        action="store", default=None)
    parser.add_argument("-k", "--keepalive", dest="keepalive",
                        help="Keep the process alive even after all the DHCP clients have been processed",
                        action="store_true", default=False)
    
    options = parser.parse_args()

    if options.interface == None:
        raise RuntimeError("Outgoing interface not provided")

    if (options.start_mac_addr == None) and (options.test == None):
        raise RuntimeError("Start mac address not provided")

    DEBUG = options.debug
    ERROR = options.error
    print "SLEEP_SEC: " + str(SLEEP_SEC)

    dhcp_tool = DHCPTool(options.start_mac_addr, options.interface, options.count,
                         options.test, options.rate)

    if options.test != None:
        tmp_list = options.test.split("^")
        TEST_IP = tmp_list[0]
        TEST_MAC = tmp_list[1]
        Debug("TESTING IP: %s MAC: %s" % (str(TEST_IP), str(TEST_MAC)))
        dhcp_tool._validate_ip_addr(TEST_IP)
        dhcp_tool._validate_mac_addr(TEST_MAC)
        dhcp_tool.add_ip_mapping(TEST_IP, TEST_MAC)
        dhcp_tool.start_reply_thread()
        tmp_i = 0
        while tmp_i == 0:
            time.sleep(100)
            print "here5"
    else:
        i = 0
        while i < 64:
            DEFAULT_SNAME += chr(0)
            i += 1
            
        i = 0
        while i < 128:
            DEFAULT_FILE += chr(0)
            i += 1

        try:
            dhcp_tool.start(options.interface)
            print "\n\n  # of packets put into Q = {0}\n\n".format(packet_count_put_into_Q)
        except KeyboardInterrupt:
            print " "
            dhcp_tool.generate_output()

