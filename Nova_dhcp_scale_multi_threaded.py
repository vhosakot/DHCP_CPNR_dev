#! /usr/bin/python

########
#
# This script boots/deletes VMs using "nova boot/delete" CLI in a multi-threaded environment, 4 VMs at a time concurrently.
# The number of VMs booted/deleted concurrently can be controlled by the variable concurrency_limit.
# The default value of concurrency_limit is 4.
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
import thread

if len(sys.argv) < 2:
    print "\n\n   Usage is: ./Nova_dhcp_scale_multi_threaded.py <number_of_VMs_to_boot> [-delete]"
    print "   ./Nova_dhcp_scale_multi_threaded.py 10"
    print "   ./Nova_dhcp_scale_multi_threaded.py 10 -delete\n\n"
    sys.exit(0)

vm_count = int(sys.argv[1])
poll_sleep_time = 0.5  # 500 milli seconds
poll_count = 20
concurrency_limit = 4  # How many VMs to boot/delete concurrently

start_times = [""]*vm_count
end_times_with_dhcp_ip = [""]*vm_count
vm_booted_count = 0
vm_deleted_count = 0

def boot_vm(command, vm_index):
    global start_times
    # Note current time before booting each VM
    start_times[vm_index-1] = time.time()
    os.system(command)

def delete_vm(command):
    global vm_deleted_count
    os.system(command)
    vm_deleted_count = vm_deleted_count + 1

def measure_dhcp_ip_time(command, vm_index):
    dhcp_ip_assigned = ""
    global end_times_with_dhcp_ip
    global vm_booted_count
    # Poll to check if DHCP IP is assigned to the VM
    for y in range(0, poll_count):
        f = os.popen(command)
        dhcp_ip_assigned = f.read()
        if dhcp_ip_assigned == "":
            # Sleep and poll again
            time.sleep(poll_sleep_time)
            continue
        else:
            # Note current time, DHCP IP, and stop polling
            end_time = str(time.time())
            end_times_with_dhcp_ip[vm_index-1] = end_time + "+" + dhcp_ip_assigned.strip("\n")
            vm_booted_count = vm_booted_count + 1
            time_needed = float(end_time) - start_times[vm_index-1]
            print "VM{0} booted, took {1} seconds to get {2}".format(vm_index, time_needed, dhcp_ip_assigned.strip("\n"))
            return
    if dhcp_ip_assigned == "":
        # Note current time and mark DHCP IP assigned as None
        end_time = str(time.time())
        end_times_with_dhcp_ip[vm_index-1] = end_time + "+" + "None"
        vm_booted_count = vm_booted_count + 1
        time_needed = float(end_time) - start_times[vm_index-1]
        print "\nERROR: VM{0} did NOT get DHCP IP address. Waited {1} seconds\n".format(vm_index, time_needed)

for x in range(1, vm_count+1):
    if x % concurrency_limit == 1:
        if len(sys.argv) == 3 and sys.argv[2] == "-delete":
            while vm_deleted_count != (x-1):
                pass
        else:
            while vm_booted_count != (x-1):
                pass
    vm_name = "VM" + str(x)
    if len(sys.argv) == 3 and sys.argv[2] == "-delete":
        # Delete each VM in a separate thread
        command = "nova delete " + vm_name
        print "Deleting {0}".format(vm_name)
        thread.start_new_thread(delete_vm, (command, ))
        continue
    command = "nova boot --flavor m1.nano --image cirros-0.3.2-x86_64-uec --nic net-id=8e0f0053-c6af-4ef8-905e-29a58acb7b9f "
    command = command + vm_name + " > /dev/null"
    print "Booting {0}".format(vm_name)
    # Boot each VM in a separate thread
    thread.start_new_thread(boot_vm, (command, x, ))
    # Check if DHCP IP is assigned to the VM
    command = "nova list 2> /dev/null | grep \'" + vm_name + ".*ACTIVE\' | awk \'{print substr($12,9)}\'"
    thread.start_new_thread(measure_dhcp_ip_time, (command, x, ))

# Wait until all the threads end
if len(sys.argv) == 3 and sys.argv[2] == "-delete":
    while vm_deleted_count != vm_count:
        pass
    print "\nAll VMs scheduled to be deleted\n"
    sys.exit(0)
else:
    try:
        while vm_booted_count != vm_count:
            pass
    except KeyboardInterrupt:
        # Print summary for KeyboardInterrupt (CTRL+c)
        print "\n"
        for x in range(1, vm_count+1):
            vm_name = "VM" + str(x)
            time_needed = float(end_times_with_dhcp_ip[x-1].split('+')[0]) - start_times[x-1]
            print "{0} took {1} seconds to get {2}".format(vm_name, time_needed, end_times_with_dhcp_ip[x-1].split('+')[1])
        print "\n"

# Print summary after booting VMs
print "\n"
for x in range(1, vm_count+1):
    vm_name = "VM" + str(x)
    time_needed = float(end_times_with_dhcp_ip[x-1].split('+')[0]) - start_times[x-1]
    print "{0} took {1} seconds to get {2}".format(vm_name, time_needed, end_times_with_dhcp_ip[x-1].split('+')[1])
print "\n"
