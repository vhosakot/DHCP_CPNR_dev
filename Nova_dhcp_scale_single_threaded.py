#! /usr/bin/python

########
#
# This script boots/deletes VMs using "nova boot/delete" CLI in a single-threaded environment, one VM after the other.
# This script that a Neutron network already exists. DevStack creates a network.
#
# Increase the NOVA instance quota for admin
# nova quota-update --instances 1000 --floating_ips 1000 --cores 1000 febd9e5baa3941cab1790f263cc51a6f
# nova quota-show --tenant febd9e5baa3941cab1790f263cc51a6f
#
# Usage is: ./Nova_dhcp_scale_single_threaded.py <number_of_VMs_to_boot> [-delete]
# ./Nova_dhcp_scale_single_threaded.py 10
# ./Nova_dhcp_scale_single_threaded.py 10 -delete
#
########

import sys
import os
import time

if len(sys.argv) < 2:
    print "\n\n   Usage is: ./Nova_dhcp_scale_single_threaded.py <number_of_VMs_to_boot> [-delete]"
    print "   ./Nova_dhcp_scale_single_threaded.py 10"
    print "   ./Nova_dhcp_scale_single_threaded.py 10 -delete\n\n"
    sys.exit(0)

summary = ""
vm_count = int(sys.argv[1])
poll_sleep_time = 0.5  # 500 milli seconds
poll_count = 20

for x in range(1, vm_count+1):
    vm_name = "VM" + str(x)
    if len(sys.argv) == 3 and sys.argv[2] == "-delete":
        # Delete the VM
        command = "nova delete " + vm_name
        print "Deleting {0}".format(vm_name)
        os.system(command)
        continue
    command = "nova boot --flavor m1.nano --image cirros-0.3.2-x86_64-uec --nic net-id=8e0f0053-c6af-4ef8-905e-29a58acb7b9f "
    command = command + vm_name + " > /dev/null"
    print "Booting {0}".format(vm_name)
    # Start the clock and boot the VM
    start = time.time()
    os.system(command)
    # Poll to check if DHCP IP is assigned to the VM
    command = "nova list 2> /dev/null | grep \'" + vm_name + ".*ACTIVE\' | awk \'{print substr($12,9)}\'"
    dhcp_ip_assigned = ""
    for y in range(0, poll_count):
        f = os.popen(command)
        dhcp_ip_assigned = f.read()
        dhcp_ip_assigned = dhcp_ip_assigned.strip("\n")
        if dhcp_ip_assigned == "":
            # Sleep and poll again
            time.sleep(poll_sleep_time)
            continue
        else:
            # Stop the clock and stop polling
            end = time.time()
            break
    if dhcp_ip_assigned == "":
        # Stop the clock and print the error
        end = time.time()
        msg = "ERROR: {0} did NOT get DHCP IP address. Waited {1} seconds".format(vm_name, end-start)
        print "\n" + msg + "\n"
        summary = summary + msg + "\n"
    else:
        msg = "{0} booted, took {1} seconds to get {2}".format(vm_name, end-start, dhcp_ip_assigned)
        print msg
        summary = summary + msg + "\n"

if len(sys.argv) == 3 and sys.argv[2] == "-delete":
    print "\nAll VMs scheduled to be deleted\n"
else:
    print "\n" + summary
