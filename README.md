DHCP_CPNR_dev
=============

Dev branch for DHCP CPNR project

cisco_cpnr_rest_client.py is the REST client for CPNR (Cisco Prime Network Registrar).

----------------

cpnr_test_client_not_tox.py is the script to unit-test cisco_cpnr_rest_client.py using a real CPNR server. cpnr_test_client_not_tox.py does not need tox to run. Copy cisco_cpnr_rest_client.py and cpnr_test_client_not_tox.py into the same directory and use the command below to run it.

    ./cpnr_test_client_not_tox.py

----------------

test_linux_dhcp.py is the script that uses tox and a mock REST server to unit-test cisco_cpnr_rest_client.py. test_linux_dhcp.py has 2 classes (TestCiscoCpnrRestBase and TestCiscoCpnrRest).
Below are the steps.

Down neutron code from git.

    git clone https://github.com/openstack/neutron.git

Install tox.

    apt-get install python-pip

    pip install tox

    https://wiki.openstack.org/wiki/Testing

    http://docs.openstack.org/developer/neutron/devref/development.environment.html

cd into the neutron directory and make sure tox.ini file exists.

    cd neutron

Copy cisco_cpnr_rest_client.py to neutron/agent/linux/.

Copy test_linux_dhcp.py to neutron/tests/unit/.

Run the command below to unit-test cisco_cpnr_rest_client.py using tox. There are 35 unit test cases.

    ./run_tests.sh neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest

The unit tests can also be run using the command below.

    tox -e py27 neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest

----------------

Below is the expected output of tox.

neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_badconnect_to_cpnr_failure
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_badconnect_to_cpnr_failure ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_create_client_class
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_create_client_class ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_create_client_entry
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_create_client_entry ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_connect_to_cpnr
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_connect_to_cpnr ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_create_policy
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_create_policy ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_delete_client_class
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_delete_client_class ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_delete_vpn
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_delete_vpn ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_create_scope
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_create_scope ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_delete_policy
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_delete_policy ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_get_nonexistent_client_entry_failure
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_get_nonexistent_client_entry_failure ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_create_vpn
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_create_vpn ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_delete_scope
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_delete_scope ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_get_client_class
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_get_client_class ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_get_nonexistent_vpn_failure
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_get_nonexistent_vpn_failure ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_get_client_entry
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_get_client_entry ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_delete_client_entry
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_delete_client_entry ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_get_client_classes
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_get_client_classes ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_get_vpns
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_get_vpns ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_get_policy
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_get_policy ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_get_client_enties
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_get_client_enties ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_get_vpn
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_get_vpn ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_update_client_class
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_update_client_class ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_delete_nonexistent_vpn_failure
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_delete_nonexistent_vpn_failure ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_get_scope
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_get_scope ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_get_dhcp_server
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_get_dhcp_server ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_post_already_exists_failure
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_post_already_exists_failure ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_post_empty_data_failure
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_post_empty_data_failure ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_get_policies
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_get_policies ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_update_policy
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_update_policy ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_get_scopes
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_get_scopes ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_update_scope
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_update_scope ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_update_client_entry
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_update_client_entry ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_update_vpn
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_update_vpn ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_update_dhcp_server
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_update_dhcp_server ... ok
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_update_nonexistent_vpn_failure
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_update_nonexistent_vpn_failure ... ok
Slowest Tests
Test id                                                                                   Runtime (s)
----------------------------------------------------------------------------------------  -----------
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_connect_to_cpnr                 0.174
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_badconnect_to_cpnr_failure      0.168
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_create_client_class             0.126
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_create_client_entry             0.103
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_create_vpn                      0.015
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_delete_nonexistent_vpn_failure  0.014
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_delete_client_entry             0.013
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_update_dhcp_server              0.011
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_update_client_entry             0.010
neutron.tests.unit.test_linux_dhcp.TestCiscoCpnrRest.test_update_nonexistent_vpn_failure  0.010

----------------------------------------------------------------------
Ran 35 tests in 23.401s

OK
localadmin@ubuntu-14-4:~/devstack/neutron_code/neutron$ 
