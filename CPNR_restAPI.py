#! /usr/bin/python

########
# Module that implements REST APIs for the CPNR (Cisco Prime Network Registrar) server
########

import json
import requests
from requests.auth import HTTPBasicAuth

class CPNR_restApi:
    """
    Class implementing REST APIs for 
    the CPNR (Cisco Prime Network Registrar) server
    """

    def __init__(self, CPNR_server_ip, CPNR_server_port, CPNR_server_username, CPNR_server_password):
        """Constructor for the CPNR_restApi class"""
        # Should CPNR_server_ip and CPNR_server_port be validated ?
        self.CPNR_server_ip = CPNR_server_ip
        self.CPNR_server_port = CPNR_server_port
        self.CPNR_server_username = CPNR_server_username
        self.url = "http://" + self.CPNR_server_ip + ":" + str(self.CPNR_server_port) + "/"
        self.auth = HTTPBasicAuth(CPNR_server_username, CPNR_server_password)
        self.headers = {'Content-Type': 'application/json' , 'Accept': 'application/json'}

    def __repr__(self):
        """__repr__ for the CPNR_restApi class"""
        return ("<CPNR_restApi(CPNR_server_ip=%s, CPNR_server_port=%s, CPNR_server_username=%s)>" %
            (self.CPNR_server_ip, self.CPNR_server_port, self.CPNR_server_username))

    def get_DHCPServer(self):
        """Returns a dictionary with all the objects of DHCPServer"""
        request_url = self.url + "web-services/rest/resource/DHCPServer"
        r = requests.request('GET', request_url, auth=self.auth, headers=self.headers)
        # print r.json()
        return r.json()

    def get_policies(self):
        """Returns a list of all the policies from CPNR server"""
        request_url = self.url + "web-services/rest/resource/Policy"
        r = requests.request('GET', request_url, auth=self.auth, headers=self.headers)
        # print r.json()
        return r.json()

    def get_policy(self, policy_name):
        """Returns a dictionary with all the objects of a specific policy name from CPNR server"""
        request_url = self.url + "web-services/rest/resource/Policy/" + policy_name
        r = requests.request('GET', request_url, auth=self.auth, headers=self.headers)
        # print r.json()
        return r.json()

    def get_client_classes(self):
        """Returns a list of all the client classes from CPNR server"""
        request_url = self.url + "web-services/rest/resource/ClientClass"
        r = requests.request('GET', request_url, auth=self.auth, headers=self.headers)
        # print r.json()
        return r.json()

    def get_client_class(self):
        # Add later
        pass

    def get_vpns(self):
        """Returns a list of all the VPNs from CPNR server"""
        request_url = self.url + "web-services/rest/resource/VPN"
        r = requests.request('GET', request_url, auth=self.auth, headers=self.headers)
        # print r.json()
        return r.json()

    def get_vpn(self):
        # Add later
        pass

    def get_scopes(self):
        """Returns a list of all the scopes from CPNR server"""
        request_url = self.url + "web-services/rest/resource/Scope"
        r = requests.request('GET', request_url, auth=self.auth, headers=self.headers)
        # print r.json()
        return r.json()

    def get_scope(self):
        # Add later
        pass

    def get_client_entries(self):
        """Returns a list of all the client entries from CPNR server"""
        request_url = self.url + "web-services/rest/resource/ClientEntry"
        r = requests.request('GET', request_url, auth=self.auth, headers=self.headers)
        # print r.json()
        return r.json()

    def get_client_entry(self):
        # Add later
        pass

    def create_policy(self, data):
        """Returns status code after creating a policy with data dictionary"""
        request_url = self.url + "web-services/rest/resource/Policy"
        json_dump = json.dumps(data)
        r = requests.request('POST', request_url, data=json_dump, auth=self.auth, headers=self.headers)
        # print r.status_code
        print r.text
        return r.status_code

    def create_scope(self, data):
        """Returns status code after creating a scope with data dictionary"""
        request_url = self.url + "web-services/rest/resource/Scope"
        json_dump = json.dumps(data)
        r = requests.request('POST', request_url, data=json_dump, auth=self.auth, headers=self.headers)
        # print r.status_code
        print r.text
        return r.status_code

    def update_dhcp_server(self, data):
        """Returns status code after updating dhcp server with data dictionary"""
        request_url = self.url + "web-services/rest/resource/DHCPServer"
        json_dump = json.dumps(data)
        r = requests.request('PUT', request_url, data=json_dump, auth=self.auth, headers=self.headers)
        # print r.status_code
        print r.text
        return r.status_code

