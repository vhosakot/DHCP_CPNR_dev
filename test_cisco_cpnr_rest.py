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
#

import requests
#from requests import exceptions as r_exc
from requests_mock.contrib import fixture as mock_fixture

from neutron.agent.linux import (
    cisco_cpnr_rest_client as cpnr_client)
from neutron.tests import base

CPNRip = "localhost"
CPNRport = "8080"
CPNRusername = "cpnradmin"
CPNRpassword = "password"
LOCAL_URL = "http://" + CPNRip + ":" + CPNRport
URL_BASE = "/web-services/rest/resource/"
REQUEST_URL = LOCAL_URL + URL_BASE


class CiscoCpnrBaseTestCase(base.BaseTestCase):

    """Helper methods to register mock intercepts - used by child classes."""

    def setUp(self):
        super(CiscoCpnrBaseTestCase, self).setUp()
        self.requests = self.useFixture(mock_fixture.Fixture())
        self.cpnr = cpnr_client.CpnrRestClient(CPNRip,
            CPNRport, CPNRusername, CPNRpassword)
        dir(self.cpnr)

    def _register_local_get(self, uri, json=None,
                            result_code=requests.codes.OK):
        self.requests.register_uri(
            'GET',
            REQUEST_URL + uri,
            status_code=result_code,
            json=json)

    def _register_local_post(self, uri, resource_id,
                             result_code=requests.codes.CREATED):
        self.requests.register_uri(
            'POST',
            LOCAL_URL + uri,
            status_code=result_code,
            headers={'location': LOCAL_URL + uri + '/' + str(resource_id)})

    def _register_local_delete(self, uri, resource_id, json=None,
                               result_code=requests.codes.NO_CONTENT):
        self.requests.register_uri(
            'DELETE',
            LOCAL_URL + uri + '/' + str(resource_id),
            status_code=result_code,
            json=json)

    def _register_local_put(self, uri, resource_id,
                            result_code=requests.codes.NO_CONTENT):
        self.requests.register_uri('PUT',
                                   LOCAL_URL + uri + '/' + resource_id,
                                   status_code=result_code)

    def _register_local_get_not_found(self, uri, resource_id,
                                      result_code=requests.codes.NOT_FOUND):
        self.requests.register_uri(
            'GET',
            LOCAL_URL + uri + '/' + str(resource_id),
            status_code=result_code)


class TestCpnrGetRestApi(CiscoCpnrBaseTestCase):

    def test_get_dhcp_server(self):
        """Test get_dhcp_server"""
        self._register_local_get("DHCPServer",
                                 json={u'clientClass': u'disabled',
                                       u'name': u'DHCP',
                                       u'objectOid':
                                       u'OID-00:00:00:00:00:00:00:06',
                                       u'deleteOrphanedLeases': u'false'})
        actual = self.cpnr.get_dhcp_server()
        self.assertIn('name', actual)
        self.assertIsNotNone(actual['name'])

    def test_get_policies(self):
        """Test get_policies"""
        self._register_local_get("Policy",
                                 json={u'name': u'default',
                                       u'gracePeriod': u'5m',
                                       u'tenantId': u'0',
                                       u'offerTimeout': u'2m',
                                       u'optionList': {u'OptionItem':
                                       [{u'number': u'51',
                                       u'value': u'00:09:3a:80'}]},
                                       u'objectOid':
                                       u'OID-00:00:00:00:00:00:00:04'})
        actual = self.cpnr.get_policies()
        self.assertIn('name', actual)
        self.assertIsNotNone(actual['name'])

    def test_get_client_classes(self):
        """Test get_client_classes"""
        self._register_local_get("ClientClass",
                                 json={})
        actual = self.cpnr.get_client_classes()
        self.assertEqual({}, actual)

    def test_get_vpns(self):
        """Test get_vpns"""
        self._register_local_get("VPN",
                                 json={})
        actual = self.cpnr.get_vpns()
        self.assertEqual({}, actual)

    def test_get_scopes(self):
        """Test get_scopes"""
        self._register_local_get("Scope",
                                 json={})
        actual = self.cpnr.get_scopes()
        self.assertEqual({}, actual)

    def test_get_client_entries(self):
        """Test get_client_entries"""
        self._register_local_get("ClientEntry",
                                 json={})
        actual = self.cpnr.get_client_entries()
        self.assertEqual({}, actual)
