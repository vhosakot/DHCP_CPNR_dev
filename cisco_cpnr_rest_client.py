# Copyright 2014 Cisco Systems, Inc.  All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

#######################################################
# Module that implements REST APIs for
# Cisco's CPNR (Cisco Prime Network Registrar) server
#######################################################

import requests
from requests import exceptions as r_exc
import time

from neutron.openstack.common.gettextutils import _LE, _LW
from neutron.openstack.common import jsonutils
from neutron.openstack.common import log as logging

LOG = logging.getLogger(__name__)
URL_BASE = "web-services/rest/resource"


class CpnrRestClient:
    """Class implementing REST APIs for
    the CPNR (Cisco Prime Network Registrar) server
    """

    def __init__(self, CPNR_server_ip, CPNR_server_port, CPNR_server_username,
                 CPNR_server_password, timeout=20):
        """Constructor for the CPNR_restApi class"""
        try:
            info = "CPNR_server_ip = " + CPNR_server_ip + ", " + \
                   "CPNR_server_port = " +\
                   str(CPNR_server_port) + ", " + \
                   "CPNR_server_username = " +\
                   CPNR_server_username + ", " + \
                   "timeout = " + str(timeout)
            LOG.debug("info = {0}".format(info))
            self.CPNR_server_ip = CPNR_server_ip
            self.CPNR_server_port = CPNR_server_port
            self.CPNR_server_username = CPNR_server_username
            self.url = "http://" + self.CPNR_server_ip + ":" + \
                       str(self.CPNR_server_port)
            self.auth = requests.auth.HTTPBasicAuth(CPNR_server_username,
                        CPNR_server_password)
            self.headers = {'Content-Type': 'application/json',
                            'Accept': 'application/json'}
            self._cpnr_reload_needed = False
            self.timeout = timeout
            cpnr_server = self.get_dhcp_server()
            LOG.debug("cpnr_server = {0}".format(cpnr_server))
        except Exception as e:
            LOG.error(_LE("Unexpected error in constructor,"
                "%(ex_type)s, %(ex_args)s. %(ex_info)s)"),
                {'ex_type': str(type(e)),
                 'ex_args': str(e.args),
                 'ex_info': str(info)})

    def __repr__(self):
        """__repr__ for the CPNR_restApi class"""
        return ("<CPNR_restApi(CPNR_server_ip=%s, CPNR_server_port=%s, "
            "CPNR_server_username=%s, timeout=%s)>" %
            (self.CPNR_server_ip, self.CPNR_server_port,
            self.CPNR_server_username, self.timeout))

    def _build_url(self, tag):
        """Builds and returns REST url"""
        rest_url = [self.url, URL_BASE]
        rest_url.extend(tag)
        return "/".join(rest_url)

    def _do_request(self, method, request_url, data=None, reload_needed=False):
        """Perform REST request and return response"""
        try:
            info = "method = " + method + ", " + \
                   "request_url = " + request_url + ", " + \
                   "\ndata = " + str(data) + ", " + \
                   "\nreload_needed = " + str(reload_needed) + ", " + \
                   "CPNR_server_ip = " + self.CPNR_server_ip + ", " + \
                   "CPNR_server_port = " +\
                   str(self.CPNR_server_port) + ", " + \
                   "CPNR_server_username = " +\
                   self.CPNR_server_username + ", " + \
                   "timeout = " + str(self.timeout)
            LOG.debug("info = {0}".format(info))
            if method == 'GET' or method == 'DELETE':
                start_time = time.time()
                response = requests.request(method, request_url,
                           auth=self.auth, headers=self.headers,
                           timeout=self.timeout)
                LOG.debug("%(method)s Took %(time).2f seconds to process",
                      {'method': method,
                       'time': time.time() - start_time})
                if response.status_code != requests.codes.ok:
                    raise Exception("Invalid return code {0}".
                        format(response.status_code), "Expected return code \
                        for {0} is {1}".format(method, requests.codes.ok))
            elif method == 'POST' or method == 'PUT':
                if data is None:
                    raise Exception("data dictionary is empty for {0}".
                        format(method))
                json_dump = jsonutils.dumps(data)
                start_time = time.time()
                response = requests.request(method, request_url,
                           data=json_dump, auth=self.auth,
                           headers=self.headers, timeout=self.timeout)
                LOG.debug("%(method)s Took %(time).2f seconds to process",
                      {'method': method,
                       'time': time.time() - start_time})
                if method == 'POST':
                    if response.status_code != requests.codes.created:
                        raise Exception("Invalid return code {0}".
                            format(response.status_code), "Expected return \
                            code for POST is {0}".
                            format(requests.codes.created))
                else:
                    if response.status_code != requests.codes.ok:
                        raise Exception("Invalid return code {0}".
                            format(response.status_code), "Expected return \
                            code for PUT is {0}".format(requests.codes.ok))
            LOG.debug("response.text = {0}".format(response.text))
        except r_exc.Timeout as te:
            LOG.warning(_LW("Request timeout for CPNR,"
                "%(ex_type)s, %(ex_args)s. %(ex_info)s)"),
                {'ex_type': str(type(te)),
                 'ex_args': str(te.args),
                 'ex_info': str(info)})
        except r_exc.ConnectionError as ce:
            LOG.exception(_LE("Unable to connect to CPNR,"
                "%(ex_type)s, %(ex_args)s. %(ex_info)s)"),
                {'ex_type': str(type(ce)),
                 'ex_args': str(ce.args),
                 'ex_info': str(info)})
        except Exception as e:
            LOG.error(_LE("Unexpected error with CPNR,"
                "%(ex_type)s, %(ex_args)s. %(ex_info)s)"),
                {'ex_type': str(type(e)),
                 'ex_args': str(e.args),
                 'ex_info': str(info)})
        else:
            if method == 'GET':
                LOG.debug("response.json() = {0}".format(response.json()))
                # print response.json()
                return response.json()
            elif method == 'POST' or method == 'PUT' or method == 'DELETE':
                LOG.debug("response.status_code =  {0}".
                    format(response.status_code))
                # print response.text
                if reload_needed is True:
                    self._cpnr_reload_needed = True
                elif 'Scope' in request_url:
                    if "AX_DHCP_RELOAD_REQUIRED" in response.content:
                        self._cpnr_reload_needed = True
                return response.status_code
            LOG.debug("{0} request completed. Return code = {1}".
                format(method, response.status_code))

    def get_dhcp_server(self):
        """Returns a dictionary with all the objects of DHCPServer"""
        request_url = self._build_url(['DHCPServer'])
        return self._do_request('GET', request_url)

    def get_policies(self):
        """Returns a list of all the policies from CPNR server"""
        request_url = self._build_url(['Policy'])
        return self._do_request('GET', request_url)

    def get_policy(self, policy_name):
        """Returns a dictionary with all the objects of a specific policy
        name from CPNR server
        """
        request_url = self._build_url(['Policy', policy_name])
        return self._do_request('GET', request_url)

    def get_client_classes(self):
        """Returns a list of all the client classes from CPNR server"""
        request_url = self._build_url(['ClientClass'])
        return self._do_request('GET', request_url)

    def get_client_class(self, client_class_name):
        """Returns a dictionary with all the objects of a specific client
        class name from CPNR server
        """
        request_url = self._build_url(['ClientClass', client_class_name])
        return self._do_request('GET', request_url)

    def get_vpns(self):
        """Returns a list of all the VPNs from CPNR server"""
        request_url = self._build_url(['VPN'])
        return self._do_request('GET', request_url)

    def get_vpn(self, vpn_name):
        """Returns a dictionary with all the objects of a specific VPN name
        from CPNR server
        """
        request_url = self._build_url(['VPN', vpn_name])
        return self._do_request('GET', request_url)

    def get_scopes(self):
        """Returns a list of all the scopes from CPNR server"""
        request_url = self._build_url(['Scope'])
        return self._do_request('GET', request_url)

    def get_scope(self, scope_name):
        """Returns a dictionary with all the objects of a specific scope name
        from CPNR server
        """
        request_url = self._build_url(['Scope', scope_name])
        return self._do_request('GET', request_url)

    def get_client_entries(self):
        """Returns a list of all the client entries from CPNR server"""
        request_url = self._build_url(['ClientEntry'])
        return self._do_request('GET', request_url)

    def get_client_entry(self, client_entry_name):
        """Returns a dictionary with all the objects of a specific client
        entry name from CPNR server
        """
        request_url = self._build_url(['ClientEntry', client_entry_name])
        return self._do_request('GET', request_url)

    def get_leases(self):
        """Returns a list of all the leases from CPNR server"""
        request_url = self._build_url(['Lease'])
        return self._do_request('GET', request_url)

    def create_policy(self, data):
        """Returns status code after creating a policy with data dictionary"""
        request_url = self._build_url(['Policy'])
        return self._do_request('POST', request_url, data, True)

    def create_scope(self, data):
        """Returns status code after creating a scope with data dictionary"""
        request_url = self._build_url(['Scope'])
        return self._do_request('POST', request_url, data)

    def create_client_class(self, data):
        """Returns status code after creating a client class with data
        dictionary
        """
        request_url = self._build_url(['ClientClass'])
        return self._do_request('POST', request_url, data, True)

    def create_vpn(self, data):
        """Returns status code after creating a VPN with data dictionary"""
        request_url = self._build_url(['VPN'])
        return self._do_request('POST', request_url, data, True)

    def create_client_entry(self, data):
        """Returns status code after creating a client entry with data
        dictionary
        """
        request_url = self._build_url(['ClientEntry'])
        return self._do_request('POST', request_url, data)

    def update_dhcp_server(self, data):
        """Returns status code after updating dhcp server with data
        dictionary
        """
        request_url = self._build_url(['DHCPServer'])
        return self._do_request('PUT', request_url, data, True)

    def update_policy(self, policy_name, data):
        """Returns status code after updating policy policy_name with data
        dictionary
        """
        request_url = self._build_url(['Policy', policy_name])
        return self._do_request('PUT', request_url, data, True)

    def update_client_class(self, client_class_name, data):
        """Returns status code after updating client class client_class_name
        with data dictionary
        """
        request_url = self._build_url(['ClientClass', client_class_name])
        return self._do_request('PUT', request_url, data, True)

    def update_vpn(self, vpn_name, data):
        """Returns status code after updating VPN vpn_name with data
        dictionary
        """
        request_url = self._build_url(['VPN', vpn_name])
        return self._do_request('PUT', request_url, data, True)

    def update_scope(self, scope_name, data):
        """Returns status code after updating scope scope_name with data
        dictionary
        """
        request_url = self._build_url(['Scope', scope_name])
        return self._do_request('PUT', request_url, data)

    def update_client_entry(self, client_entry_name, data):
        """Returns status code after updating client entry client_entry_name
        with data dictionary
        """
        request_url = self._build_url(['ClientEntry', client_entry_name])
        return self._do_request('PUT', request_url, data)

    def delete_policy(self, policy_name):
        """Returns status code after deleting policy policy_name"""
        request_url = self._build_url(['Policy', policy_name])
        return self._do_request('DELETE', request_url, reload_needed=True)

    def delete_client_class(self, client_class_name):
        """Returns status code after deleting client class client_class_name"""
        request_url = self._build_url(['ClientClass', client_class_name])
        return self._do_request('DELETE', request_url, reload_needed=True)

    def delete_vpn(self, vpn_name):
        """Returns status code after deleting VPN vpn_name
        delete_vpn must not be called before delete_client_entry
        """
        request_url = self._build_url(['VPN', vpn_name])
        return self._do_request('DELETE', request_url, reload_needed=True)

    def delete_scope(self, scope_name):
        """Returns status code after deleting scope scope_name"""
        request_url = self._build_url(['Scope', scope_name])
        return self._do_request('DELETE', request_url)

    def delete_client_entry(self, client_entry_name):
        """Returns status code after deleting scope client_entry_name
        delete_vpn must not be called before delete_client_entry
        """
        request_url = self._build_url(['ClientEntry', client_entry_name])
        # ClientEntry = self.get_client_entry(client_entry_name)
        # print "ClientEntry's reservedAddresses = {0}".format\
        # (ClientEntry['reservedAddresses']['stringItem'][0])
        # print "ClientEntry's vpnId in name = {0}".format\
        # ((ClientEntry['name']).split('-')[0])
        return self._do_request('DELETE', request_url)

        # After deleting the client entry, call the releaseAddress special
        # function with VPN ID in 'name' and 'reservedAddresses'
        # The command below does not work due to a CPNR bug.
        # Email sent to CPNR team.
        # curl -u admin:changeme -X DELETE \
        # http://localhost:8888/web-services/rest/resource/Lease/10.10.0.21\
        # ?action=releaseAddress&vpnId=30

    def reload_cpnr_server(self):
        """Returns status code after reloading CPNR server"""
        try:
            request_url = self._build_url(['DHCPServer',
                '?action=reloadServer'])
            info = "method = " + "PUT" + ", " + \
                   "request_url = " + request_url + ", " + \
                   "CPNR_server_ip = " + self.CPNR_server_ip + ", " + \
                   "CPNR_server_port = " +\
                   str(self.CPNR_server_port) + ", " + \
                   "CPNR_server_username = " +\
                   self.CPNR_server_username + ", " + \
                   "timeout = " + str(self.timeout)
            LOG.debug("info = {0}".format(info))
            LOG.debug("_cpnr_reload_needed = {0}".
                format(self._cpnr_reload_needed))
            r = requests.request('PUT', request_url, auth=self.auth)
            # print r.status_code
            self._cpnr_reload_needed = False
            # print r.text
            return r.status_code
        except Exception as e:
            LOG.error(_LE("Unexpected error in reload_cpnr_server,"
                "%(ex_type)s, %(ex_args)s. %(ex_info)s)"),
                {'ex_type': str(type(e)),
                 'ex_args': str(e.args),
                 'ex_info': str(info)})

    def get_cpnr_version(self):
        """Returns the CPNR version"""
        try:
            request_url = "/".join([self.url, "web-services/rest/session"])
            info = "method = " + "GET" + ", " + \
                   "request_url = " + request_url + ", " + \
                   "CPNR_server_ip = " + self.CPNR_server_ip + ", " + \
                   "CPNR_server_port = " +\
                   str(self.CPNR_server_port) + ", " + \
                   "CPNR_server_username = " +\
                   self.CPNR_server_username + ", " + \
                   "timeout = " + str(self.timeout)
            LOG.debug("info = {0}".format(info))
            LOG.debug("_cpnr_reload_needed = {0}".
                format(self._cpnr_reload_needed))
            r = requests.request('GET', request_url, auth=self.auth)
            # print r.status_code
            return str(r.text)
        except Exception as e:
            LOG.error(_LE("Unexpected error in get_cpnr_version,"
                "%(ex_type)s, %(ex_args)s. %(ex_info)s)"),
                {'ex_type': str(type(e)),
                 'ex_args': str(e.args),
                 'ex_info': str(info)})
