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

    def get_dhcp_server(self):
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

    def get_client_class(self, client_class_name):
        """Returns a dictionary with all the objects of a specific client class name from CPNR server"""
        request_url = self.url + "web-services/rest/resource/ClientClass/" + client_class_name
        r = requests.request('GET', request_url, auth=self.auth, headers=self.headers)
        # print r.json()
        return r.json()

    def get_vpns(self):
        """Returns a list of all the VPNs from CPNR server"""
        request_url = self.url + "web-services/rest/resource/VPN"
        r = requests.request('GET', request_url, auth=self.auth, headers=self.headers)
        # print r.json()
        return r.json()

    def get_vpn(self, vpn_name):
        """Returns a dictionary with all the objects of a specific VPN name from CPNR server"""
        request_url = self.url + "web-services/rest/resource/VPN/" + vpn_name
        r = requests.request('GET', request_url, auth=self.auth, headers=self.headers)
        # print r.json()
        return r.json()

    def get_scopes(self):
        """Returns a list of all the scopes from CPNR server"""
        request_url = self.url + "web-services/rest/resource/Scope"
        r = requests.request('GET', request_url, auth=self.auth, headers=self.headers)
        # print r.json()
        return r.json()

    def get_scope(self, scope_name):
        """Returns a dictionary with all the objects of a specific scope name from CPNR server"""
        request_url = self.url + "web-services/rest/resource/Scope/" + scope_name
        r = requests.request('GET', request_url, auth=self.auth, headers=self.headers)
        # print r.json()
        return r.json()

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

    def create_client_class(self, data):
        """Returns status code after creating a client class with data dictionary"""
        request_url = self.url + "web-services/rest/resource/ClientClass"
        json_dump = json.dumps(data)
        r = requests.request('POST', request_url, data=json_dump, auth=self.auth, headers=self.headers)
        # print r.status_code
        print r.text
        return r.status_code

    def create_vpn(self, data):
        """Returns status code after creating a VPN with data dictionary"""
        request_url = self.url + "web-services/rest/resource/VPN"
        json_dump = json.dumps(data)
        r = requests.request('POST', request_url, data=json_dump, auth=self.auth, headers=self.headers)
        # print r.status_code
        print r.text
        return r.status_code

    def create_client_entry(self, data):
        """Returns status code after creating a client entry with data dictionary"""
        request_url = self.url + "web-services/rest/resource/ClientEntry"
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

    def update_policy(self, policy_name, data):
        """Returns status code after updating policy policy_name with data dictionary"""
        request_url = self.url + "web-services/rest/resource/Policy/" + policy_name
        json_dump = json.dumps(data)
        r = requests.request('PUT', request_url, data=json_dump, auth=self.auth, headers=self.headers)
        # print r.status_code
        print r.text
        return r.status_code

    def update_client_class(self, client_class_name, data):
        """Returns status code after updating client class client_class_name with data dictionary"""
        request_url = self.url + "web-services/rest/resource/ClientClass/" + client_class_name
        json_dump = json.dumps(data)
        r = requests.request('PUT', request_url, data=json_dump, auth=self.auth, headers=self.headers)
        # print r.status_code
        print r.text
        return r.status_code

    def update_vpn(self, vpn_name, data):
        """Returns status code after updating VPN vpn_name with data dictionary"""
        request_url = self.url + "web-services/rest/resource/VPN/" + vpn_name
        json_dump = json.dumps(data)
        r = requests.request('PUT', request_url, data=json_dump, auth=self.auth, headers=self.headers)
        # print r.status_code
        print r.text
        return r.status_code

    def update_scope(self, scope_name, data):
        """Returns status code after updating scope scope_name with data dictionary"""
        request_url = self.url + "web-services/rest/resource/Scope/" + scope_name
        json_dump = json.dumps(data)
        r = requests.request('PUT', request_url, data=json_dump, auth=self.auth, headers=self.headers)
        # print r.status_code
        print r.text
        return r.status_code

    def delete_policy(self, policy_name):
        """Returns status code after deleting policy policy_name"""
        request_url = self.url + "web-services/rest/resource/Policy/" + policy_name
        r = requests.request('DELETE', request_url, auth=self.auth, headers=self.headers)
        # print r.status_code
        print r.text
        return r.status_code

    def delete_client_class(self, client_class_name):
        """Returns status code after deleting client class client_class_name"""
        request_url = self.url + "web-services/rest/resource/ClientClass/" + client_class_name
        r = requests.request('DELETE', request_url, auth=self.auth, headers=self.headers)
        # print r.status_code
        print r.text
        return r.status_code

    def delete_vpn(self, vpn_name):
        """Returns status code after deleting VPN vpn_name"""
        request_url = self.url + "web-services/rest/resource/VPN/" + vpn_name
        r = requests.request('DELETE', request_url, auth=self.auth, headers=self.headers)
        # print r.status_code
        print r.text
        return r.status_code

