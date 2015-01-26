#! /usr/bin/python

################
#
# This script
#  1. Will SSH into the VM created by boot_dhcp_vm.py.
#  2. Bounce all the DHCP interfaces.
#  3. Measure the time needed by all the DHCP interfaces to get
#     their DHCP IP addresses from the DHCP server.
#  4. Measure CPU and memory usage of neutron-server and neutron-dhcp-agent
#
# This script will save the CPU and memory usage numbers in a file with name
# dhcp_scale_cpu_memory_<timestamp>.log in the current directory.
#
################

import os
import sys
import time
import thread
from pexpect import *
from neutronclient.v2_0 import client as neutron_client
from novaclient.client import Client as nova_client

def get_neutron_credentials():
    d = {}
    d['username'] = os.environ['OS_USERNAME']
    d['password'] = os.environ['OS_PASSWORD']
    d['auth_url'] = os.environ['OS_AUTH_URL']
    d['tenant_name'] = os.environ['OS_TENANT_NAME']
    return d

def get_nova_credentials_v2():
    d = {}
    d['version'] = '2'
    d['username'] = os.environ['OS_USERNAME']
    d['api_key'] = os.environ['OS_PASSWORD']
    d['auth_url'] = os.environ['OS_AUTH_URL']
    d['project_id'] = os.environ['OS_TENANT_NAME']
    return d

# Get DevStack neutron credentials
neutron_credentials = get_neutron_credentials()

# Initialize Neutron client
neutron = neutron_client.Client(**neutron_credentials)

# Get DevStack nova credentials
nova_credentials = get_nova_credentials_v2()

# Initialize Nova client
nova = nova_client(**nova_credentials)

script_ended = False
filename = ""

def measure_cpu_memory():
    global script_ended
    global filename
    filename = "dhcp_scale_cpu_memory_" + time.strftime("%m%d%Y_%H%M%S") + '.log'
    cpu_mem_file = open(filename, 'w')
    neutron_server_cpu_mem_dict = {'pid':"", 'cpu':[], 'memory':[]}
    neutron_dhcp_agent_cpu_mem_dict = {'pid':"", 'cpu':[], 'memory':[]}

    while script_ended is False:
        f = os.popen("ps -eo sz,vsize,rss,%cpu,pid,command | grep \'neutron-server\|neutron-dhcp-agent\' | grep -v grep")
        cpu_memory_output = f.read()
        cpu_mem_list = cpu_memory_output.splitlines()
        for line in cpu_mem_list:
            fields = line.split()
            if "neutron-server" in line:
                if neutron_server_cpu_mem_dict['pid'] == "":
                    neutron_server_cpu_mem_dict['pid'] = fields[4]
                neutron_server_cpu_mem_dict['cpu'].append(fields[3])
                neutron_server_cpu_mem_dict['memory'].append(
                  int(fields[0]) + int(fields[1]) + int(fields[2]))
            elif "neutron-dhcp-agent" in line:
                if neutron_dhcp_agent_cpu_mem_dict['pid'] == "":
                    neutron_dhcp_agent_cpu_mem_dict['pid'] = fields[4]
                neutron_dhcp_agent_cpu_mem_dict['cpu'].append(fields[3])
                neutron_dhcp_agent_cpu_mem_dict['memory'].append(
                  int(fields[0]) + int(fields[1]) + int(fields[2]))
        time.sleep(1)

    cpu_mem_file.write("********\nneutron-server (PID " + neutron_server_cpu_mem_dict['pid'] + ")\n")
    cpu_mem_file.write("**********************\n")
    cpu_mem_file.write("CPU usage percentage (cputime/realtime ratio)\n")
    cpu_mem_file.write("----------------\n")
    for cpu in neutron_server_cpu_mem_dict['cpu']:
        cpu_mem_file.write(cpu + "\n")
    cpu_mem_file.write("Memory usage in kB\n")
    cpu_mem_file.write("----------------\n")
    for mem in neutron_server_cpu_mem_dict['memory']:
        cpu_mem_file.write(str(mem) + "\n")

    cpu_mem_file.write("\n\n********\nneutron-dhcp-agent (PID " + neutron_dhcp_agent_cpu_mem_dict['pid'] + ")\n")
    cpu_mem_file.write("**********************\n")
    cpu_mem_file.write("CPU usage percentage (cputime/realtime ratio)\n")
    cpu_mem_file.write("----------------\n")
    for cpu in neutron_dhcp_agent_cpu_mem_dict['cpu']:
        cpu_mem_file.write(cpu + "\n")
    cpu_mem_file.write("Memory usage in kB\n")
    cpu_mem_file.write("----------------\n")
    for mem in neutron_dhcp_agent_cpu_mem_dict['memory']:
        cpu_mem_file.write(str(mem) + "\n")

    cpu_mem_file.close()

test_passed = False
unexpected_error_ouput = ""
vm_floating_ip = neutron.list_floatingips()['floatingips'][0]['floating_ip_address']

# Check if /home/ubuntu/interface_bounce.sh exists in the VM. If not, copy interface_bounce.sh into the VM using scp
command = "ssh -oStrictHostKeyChecking=no -i dhcp.pem ubuntu@" + vm_floating_ip + \
    " \'ls -lrt /home/ubuntu/interface_bounce.sh 2> /dev/null\'"
f = os.popen(command)
output = f.read()
if output == "":
    command = "scp -oStrictHostKeyChecking=no -i dhcp.pem interface_bounce.sh ubuntu@" + \
        vm_floating_ip + ":/home/ubuntu/"
    os.system(command)

# SSH into the VM dhcp-scale-vm
ssh_command = "ssh -oStrictHostKeyChecking=no -i dhcp.pem ubuntu@" + vm_floating_ip
child = spawn(ssh_command, timeout=600, logfile = sys.stdout)
child.expect('ubuntu@dhcp-scale-vm.*')

# Check if '127.0.0.1 dhcp-scale-vm' exists in /etc/hosts
command_output = ""
child.sendline('grep dhcp-scale-vm /etc/hosts')
expect_result = child.expect('ubuntu@dhcp-scale-vm.*')
if len(child.before.splitlines()) >= 2:
    command_output = child.before.splitlines()[1]
if "127.0.0.1" in command_output and "dhcp-scale-vm" in command_output:
    pass
else:
    child.sendline("sudo bash -c \'echo -e \"\\n127.0.0.1 dhcp-scale-vm\" >> /etc/hosts\' 2> /dev/null")
    child.expect('ubuntu@dhcp-scale-vm.*')

child.sendline('chmod 777 /home/ubuntu/interface_bounce.sh')
child.expect('ubuntu@dhcp-scale-vm.*')

# Find the number of DHCP interfaces that must be bounced on the VM
VM = nova.servers.list()[0]
vm_addresses_dict = VM.__dict__['addresses']
vm_mac_ip_list = []

for key, value in vm_addresses_dict.iteritems():
    mac_ip = {'mac_addr':value[0]['OS-EXT-IPS-MAC:mac_addr'], 'ip':value[0]['addr']}
    vm_mac_ip_list.append(mac_ip)

vm_dhcp_bounce_interface_count = len(vm_mac_ip_list) - 1

# cd to the home directory /home/ubuntu/ in the VM
child.sendline('cd')
child.expect('ubuntu@dhcp-scale-vm.*')

# Shutdown all the DHCP interfaces and remove their IP addresses
command = "./interface_bounce.sh " + str(vm_dhcp_bounce_interface_count) + " down"
child.sendline(command)
child.expect('ubuntu@dhcp-scale-vm.*')

# Wait for 30 seconds after shutting down all the DHCP interfaces before turning them back on
child.sendline("")
child.expect('ubuntu@dhcp-scale-vm.*')
child.sendline("# Waiting for 30 seconds after shutting down all the DHCP interfaces before turning them back on")
child.expect('ubuntu@dhcp-scale-vm.*')
child.sendline("")
child.expect('ubuntu@dhcp-scale-vm.*')
time.sleep(30)

# After waiting for 30 seconds, check if all the DHCP interfaces are down and their IP addresses are removed
child.sendline("ip address")
child.expect('ubuntu@dhcp-scale-vm.*')

# Turn all DHCP interfaces back on
command = "./interface_bounce.sh " + str(vm_dhcp_bounce_interface_count) + " up"
child.sendline(command)
child.expect('ubuntu@dhcp-scale-vm.*')

# Wait for 5 seconds before running dhclient on all the DHCP interfaces
time.sleep(5)

# Check if all the interfaces are back up with no IP address
child.sendline("ip address")
child.expect('ubuntu@dhcp-scale-vm.*')

# Kill all old dhclient processes in the VM
child.sendline("sudo pkill -f dhclient")
child.expect('ubuntu@dhcp-scale-vm.*')

# Measure CPU and memory usage every second in a different thread
thread.start_new_thread(measure_cpu_memory, ())

# Start the clock and turn on all the DHCP interfaces
start = time.time()
command = "./interface_bounce.sh " + str(vm_dhcp_bounce_interface_count) + " dhclient"
child.sendline(command)
child.expect('ubuntu@dhcp-scale-vm.*')

# Check if all the DHCP interfaces are back up and have received their DHCP IP addresses
expected_number_of_lines_in_output = (vm_dhcp_bounce_interface_count + 2) * 6
time_needed = 0

while 1:
    command_output = 0
    child.sendline("ip address | wc -l")
    child.expect('ubuntu@dhcp-scale-vm.*')
    if len(child.before.splitlines()) >= 2 and child.before.splitlines()[1].isdigit():
        command_output = child.before.splitlines()[1]
    if int(command_output) != expected_number_of_lines_in_output:
        # If number of lines in the output of "ip address | wc -l" is not expected, break and process the errors
        end = time.time()
        time_needed = end - start
        test_passed = False
        child.sendline("ip address")
        child.expect('ubuntu@dhcp-scale-vm.*')
        unexpected_error_ouput = child.before.splitlines()
        break
    else:
        # The number of lines in the output of "ip address | wc -l" is correct. Note the time and break
        end = time.time()
        child.sendline("ip address")
        child.expect('ubuntu@dhcp-scale-vm.*')
        time_needed = end - start
        test_passed = True
        break

# Before exiting, generate dhclient.log on the VM dhcp-scale-VM
command = "./interface_bounce.sh " + str(vm_dhcp_bounce_interface_count) + " generate_dhclient_log"
child.sendline(command)
child.expect('ubuntu@dhcp-scale-vm.*')

# Kill all dhclient processes in the VM
child.sendline("sudo pkill -f dhclient")
child.expect('ubuntu@dhcp-scale-vm.*')

child.sendline('exit')

def find_missing_dhcp_ip(output, vm_mac_ip_list):
    global vm_dhcp_bounce_interface_count
    output.remove(output[0])
    output.remove(output[len(output) - 1])
    index = 0
    output_chunks = []
    chunk = ""
    while 1:
        if index > (len(output) - 1):
            if chunk != "":
                output_chunks.append(chunk)
            break
        else:
            line = output[index]
        if line[0].isdigit():
            if chunk != "":
                output_chunks.append(chunk)
            chunk = line
        else:
            chunk = chunk + line
        index = index + 1

    missing_dhcp_ip_count = 0

    for mac_ip in vm_mac_ip_list:
        mac_ip_found_in_output = False
        for chunk in output_chunks:
            if mac_ip['mac_addr'].lower() in chunk.lower():
                mac_ip_found_in_output = True
                if mac_ip['ip'] in chunk:
                    break
                else:
                     vm_interface_name = chunk.split(" ")[1][:-1]
                     print "\n ERROR: Interface {0} with mac address {1} did NOT receive DHCP IP {2}. "\
                     "Waited {3} seconds\n".format(vm_interface_name, mac_ip['mac_addr'],
                         mac_ip['ip'], time_needed)
                     missing_dhcp_ip_count = missing_dhcp_ip_count + 1
                     break
        if mac_ip_found_in_output is False:
            print "\n ERROR: Neutron port with mac address {0} and IP address {1} "\
            "not found on the VM\n".format(mac_ip['mac_addr'], mac_ip['ip'])
    if missing_dhcp_ip_count > 0:
        print "\n ERROR: {0} out of {1} DHCP interfaces did NOT receive IP address\n".format(missing_dhcp_ip_count,
            vm_dhcp_bounce_interface_count)

if test_passed is True:
    script_ended = True
    # Sleep for 3 seconds so the other thread running measure_cpu_memory ends
    time.sleep(3)
    print "\n  All {0} interfaces took {1} seconds to receive their "\
    "DHCP IP addresses.\n".format(vm_dhcp_bounce_interface_count, time_needed)
else:
    script_ended = True
    # Sleep for 3 seconds so the other thread running measure_cpu_memory ends
    time.sleep(3)
    find_missing_dhcp_ip(unexpected_error_ouput, vm_mac_ip_list)

print " The CPU and memory usage numbers are saved in the file\n"\
" {0} in the current directory\n".format(filename)
