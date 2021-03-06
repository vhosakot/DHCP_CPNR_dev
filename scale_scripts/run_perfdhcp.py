#! /usr/bin/python

# Usage is : ./run_perfdhcp.py [<Number of DHCP ports to churn per minute>] [<Number of DHCP networks to churn per minute>]
# Example  : ./run_perfdhcp.py
# Example  : ./run_perfdhcp.py 5 3

import os
import time
import thread
import sys
from neutronclient.v2_0 import client as neutron_client

def get_neutron_credentials():
    d = {}
    d['username'] = os.environ['OS_USERNAME']
    d['password'] = os.environ['OS_PASSWORD']
    d['auth_url'] = os.environ['OS_AUTH_URL']
    d['tenant_name'] = os.environ['OS_TENANT_NAME']
    return d

os.system("rm -rf testns*.log")
os.system("rm -rf *memory*.log")

f = os.popen("neutron net-list | grep DHCP | wc -l 2> /dev/null")
output = f.read()
output = output.splitlines()
dhcp_network_count = int(output[0])

if dhcp_network_count == 0:
    print "\n ERROR 1: run_perfdhcp.py failed with error\n"
    sys.exit(0)

f = os.popen("neutron port-list | grep DHCP | wc -l 2> /dev/null")
output = f.read()
output = output.splitlines()
dhcp_ports = int(output[0])
dhcp_ports_per_network = dhcp_ports / dhcp_network_count

if dhcp_ports_per_network == 0:
    print "\n ERROR 2: run_perfdhcp.py failed with error\n"
    sys.exit(0)

script_ended = False
cpu_filename = ""

def measure_cpu_memory():
    try:
        global script_ended
        global cpu_filename
        slept_secs = 0
        cpu_filename = "dhcp_scale_cpu_memory_" + time.strftime("%m%d%Y_%H%M%S") + '.log'
        cpu_mem_file = open(cpu_filename, 'w')
        neutron_dhcp_agent_cpu_mem_dict = {'pid':"", 'cpu':[], 'memory':[]}
        system_memory_list = []
        system_cpu_list = []
    
        while script_ended is False:
            f = os.popen("ps -eo sz,vsize,rss,%cpu,pid,command | grep \'neutron-dhcp-agent\' | grep -v grep")
            cpu_memory_output = f.read()
            cpu_mem_list = cpu_memory_output.splitlines()
            for line in cpu_mem_list:
                fields = line.split()
                if neutron_dhcp_agent_cpu_mem_dict['pid'] == "":
                    neutron_dhcp_agent_cpu_mem_dict['pid'] = fields[4]
                neutron_dhcp_agent_cpu_mem_dict['cpu'].append(fields[3])
                neutron_dhcp_agent_cpu_mem_dict['memory'].append(
                  int(fields[0]) + int(fields[1]) + int(fields[2]))
    
            f = os.popen("cat /proc/meminfo | grep -i Memfree | awk \'{print $2}\' 2> /dev/null")
            out = f.read()
            system_memory_list.append(out.splitlines()[0])
    
            f = os.popen("top -b -n 3 -d 1 | grep Cpu | tail -n 1 | awk \'{print 100 - $8}\' 2> /dev/null")
            out = f.read()
            if (out.splitlines()[0] == "100"):
                system_cpu_list.append(str("0"))
            else:
                system_cpu_list.append(out.splitlines()[0])
    
            time.sleep(1)
            slept_secs = slept_secs + 1
            # Clear neutron logs every 20 seconds
            if slept_secs == 20:
                os.system("rm -rf /var/log/neutron/*.gz")
                os.system("rm -rf /var/log/neutron/*metadata*.log")
                # os.system("> /var/log/neutron/dhcp-agent.log")
                os.system("> /var/log/neutron/server.log")
                os.system("> /var/log/neutron/openvswitch-agent.log")
                os.system("> /var/log/neutron/dnsmasq.log")
                os.system("> /var/log/neutron/dhcp-relay.log")
                os.system("> /var/log/neutron/dns-relay.log")

                slept_secs = 0
    
        avg_dhcp_agent_cpu = 0
        avg_dhcp_agent_mem = 0
    
        cpu_mem_file.write("********\nneutron-dhcp-agent (PID " + neutron_dhcp_agent_cpu_mem_dict['pid'] + ")\n")
        cpu_mem_file.write("**********************\n")
        cpu_mem_file.write("CPU usage percentage (cputime/realtime ratio)\n")
        cpu_mem_file.write("----------------\n")
        for cpu in neutron_dhcp_agent_cpu_mem_dict['cpu']:
            avg_dhcp_agent_cpu = avg_dhcp_agent_cpu + float(cpu)
            cpu_mem_file.write(cpu + "\n")
        cpu_mem_file.write("Memory usage in kB\n")
        cpu_mem_file.write("----------------\n")
        for mem in neutron_dhcp_agent_cpu_mem_dict['memory']:
            avg_dhcp_agent_mem = avg_dhcp_agent_mem + float(mem)
            cpu_mem_file.write(str(mem) + "\n")
    
        avg_dhcp_agent_cpu = avg_dhcp_agent_cpu / len(neutron_dhcp_agent_cpu_mem_dict['cpu'])
        avg_dhcp_agent_mem = avg_dhcp_agent_mem / len(neutron_dhcp_agent_cpu_mem_dict['memory'])
    
        avg_system_mem_free = 0
        cpu_mem_file.write("\n********\nTotal system memory free in kB (cat /proc/meminfo | grep -i Memfree | awk \'{print $2}\')\n")
        cpu_mem_file.write("**********************\n")
        for sys_mem in system_memory_list:
            avg_system_mem_free = avg_system_mem_free + float(sys_mem)
            cpu_mem_file.write(sys_mem + "\n")
    
        avg_system_mem_free = avg_system_mem_free / len(system_memory_list)
    
        avg_system_cpu_used = 0
        cpu_mem_file.write("\n********\nTotal system CPU used % (top -b -n 3 -d 1 | grep Cpu | tail -n 1 | awk \'{print 100 - $8}\')\n")
        cpu_mem_file.write("**********************\n")
        for sys_cpu in system_cpu_list:
            avg_system_cpu_used = avg_system_cpu_used + float(sys_cpu)
            cpu_mem_file.write(sys_cpu + "\n")
    
        avg_system_cpu_used = avg_system_cpu_used / len(system_cpu_list)
    
        cpu_mem_file.write("\nneutron-dhcp-agent average CPU usage    = " + str(avg_dhcp_agent_cpu) + " %\n")
        cpu_mem_file.write("neutron-dhcp-agent average memory usage = " + str(avg_dhcp_agent_mem) + " kB\n")
        cpu_mem_file.write("Average total system memory free        = " + str(avg_system_mem_free) + " kB\n")
        cpu_mem_file.write("Average total system CPU used %         = " + str(avg_system_cpu_used) + " %\n")
    
        cpu_mem_file.close()
    except:
        cpu_mem_file.close()
        return

def t_create_port(json):
    neutron_credentials = get_neutron_credentials()
    neutron = neutron_client.Client(**neutron_credentials)

    for j in range(0, 4):
        try:
            port = neutron.create_port(body=json)
            break
        except:
            continue

def t_delete_port(port_id):
    neutron_credentials = get_neutron_credentials()
    neutron = neutron_client.Client(**neutron_credentials)

    for j in range(0, 4):
        try:
            neutron.delete_port(port_id)
            break
        except:
            continue

def t_create_network_subnet_port(n, new_ports_new_network):
    neutron_credentials = get_neutron_credentials()
    neutron = neutron_client.Client(**neutron_credentials)

    # Create DHCP network
    network_name = "new-network-" + str(n)
    json = {'network': {'name': network_name, 'admin_state_up': True}}
    for j in range(0, 4):
        try:
            netw = neutron.create_network(body=json)
            break
        except:
            continue
    net_dict = netw['network']
    network_id = net_dict['id']

    # Create DHCP subnet
    cidr = "252." + str(n % 254) + ".0.0/16"
    gateway_ip = "252." + str(n % 254) + ".0.1"
    subnet_name = "new-subnet-" + str(n)
    json = {'subnets': [{'cidr': cidr,
                     'ip_version': 4,
                     'network_id': network_id,
                     'gateway_ip': gateway_ip,
                     'name': subnet_name}]}
    for j in range(0, 4):
        try:
            subnet = neutron.create_subnet(body=json)
            break
        except:
            continue

    # Create DHCP ports in each new network
    for j in range(0, new_ports_new_network):
        json = {'port': {
            'admin_state_up': True,
            'name': "port-in-new-network-" + str(n) + "-" + str(j),
            'network_id': network_id}}
        thread.start_new_thread(t_create_port, (json,))

networks_to_churn = 1
dhcp_ports_per_network_to_churn = 1
delay_during_port_churn = 10
delay_during_network_churn = 10

# Usage is : ./run_perfdhcp.py [<Number of DHCP ports to churn per minute>] [<Number of DHCP networks to churn per minute>]
# Example  : ./run_perfdhcp.py
# Example  : ./run_perfdhcp.py 5 3

if len(sys.argv) == 3 and sys.argv[1].isdigit() and sys.argv[2].isdigit():
    if int(sys.argv[1]) == 0:
        dhcp_ports_per_network_to_churn = 0
    else:
        delay_during_port_churn = 60 / int(sys.argv[1])

    if int(sys.argv[2]) == 0:
        networks_to_churn = 0
    else:
        delay_during_network_churn = 60 / int(sys.argv[2])

def churn_ports_in_existing_dhcp_networks():
    global script_ended
    global dhcp_network_count
    global dhcp_ports_per_network_to_churn
    network_ids = []
    n = 0

    for i in range(0, dhcp_network_count):
        network_name = "DHCP-network-" + str(i)
        for j in range(0, 4):
            try:
                network_ids.append(neutron.list_networks(name=network_name)['networks'][0]['id'])
                break
            except:
                continue

    while script_ended is False:
        # Create ports in each existing DHCP network
        for network_id in network_ids:
            for j in range(0, dhcp_ports_per_network_to_churn):
                json = {'port': {
                    'admin_state_up': True,
                    'name': "port-in-existing-network-" + str(n),
                    'network_id': network_id}}
                thread.start_new_thread(t_create_port, (json,))
                n = n + 1

        # Sleep for few seconds after creating ports
        time.sleep(delay_during_port_churn)

        # Delete ports in each existing DHCP network
        f = os.popen("neutron port-list | grep port-in-existing-network- | awk \'{print $2}\' 2> /dev/null")
        output = f.read()
        output = output.splitlines()
        for port_id in output:
            thread.start_new_thread(t_delete_port, (port_id,))

def churn_ports_in_new_dhcp_networks():
    global script_ended
    global networks_to_churn
    global dhcp_ports_per_network_to_churn
    n = 0

    while script_ended is False:
        # Create new DHCP networks, subnets and ports
        for i in range(0, networks_to_churn):
            thread.start_new_thread(t_create_network_subnet_port, (n, dhcp_ports_per_network_to_churn))
            n = n + 1

        # Sleep for few seconds after creating networks, subnets and ports
        time.sleep(delay_during_network_churn)

        # Delete ports in each new DHCP network
        f = os.popen("neutron port-list | grep port-in-new-network- | awk \'{print $2}\' 2> /dev/null")
        output = f.read()
        output = output.splitlines()
        for port_id in output:
            thread.start_new_thread(t_delete_port, (port_id,))

        # Sleep after deleting ports
        time.sleep(2)

        # Delete new DHCP subnets
        f = os.popen("neutron subnet-list | grep new-subnet- | awk \'{print $2}\' 2> /dev/null")
        output = f.read()
        output = output.splitlines()
        for subnet_id in output:
            try:
                neutron.delete_subnet(subnet_id)
            except:
                pass

        # Delete new DHCP networks
        f = os.popen("neutron net-list | grep new-network- | awk \'{print $2}\' 2> /dev/null")
        output = f.read()
        output = output.splitlines()
        for network_id in output:
            ns = "qdhcp-" + network_id
            try:
                neutron.delete_network(network_id)
                os.system("sudo ip netns delete " + ns + " &> /dev/null")
            except:
                os.system("sudo ip netns delete " + ns + " &> /dev/null")
                pass

# Start measuring CPU and memory usage in a separate thread before running perfdhcp
thread.start_new_thread(measure_cpu_memory, ())

# Start port churn and network churn in a separate thread before running perfdhcp
thread.start_new_thread(churn_ports_in_existing_dhcp_networks, ())
thread.start_new_thread(churn_ports_in_new_dhcp_networks, ())

for i in range(0, dhcp_network_count):
    testns = "testns-DHCP-network-" + str(i)
    logfile = testns + "_" + str(dhcp_ports_per_network) + "_" + time.strftime("%m%d%Y_%H%M%S") + ".log"
    cmd = "sudo ip netns exec " + testns + " ip a | grep tap"
    f = os.popen(cmd)
    output = f.read()
    output = output.splitlines()
    test_tap_interface = output[0].split()[1].split(':')[0]

    cmd = "sudo ip netns exec " + testns + " /usr/local/sbin/perfdhcp -4 -b mac=fa:16:00:00:00:00 -r " + str(dhcp_ports_per_network) + " -R " + str(dhcp_ports_per_network) + " -p 120" + " -l " + test_tap_interface + " &> " + logfile + " &"
    print "\n" + cmd
    os.system(cmd)

# Wait for perfdhcp in all test namespaces to complete
print "\nWaiting for perfdhcp in all test namespaces to complete....\n"
while True:
    f = os.popen("ps aux | grep perfdhcp | grep -v 'grep\|run_perfdhcp'")
    output = f.read()
    output = output.splitlines()
    if output == []:
        script_ended = True
        break
    else:
        time.sleep(1)

print "perfdhcp ended\n"

# Wait for measure_cpu_memory and port-churn and network-churn
# running in a separate thread to stop
time.sleep(10)

neutron_credentials = get_neutron_credentials()
neutron = neutron_client.Client(**neutron_credentials)

# Delete remaining churned networks, subnets and ports

print "Deleting remaining churned networks, subnets and ports\n"

f = os.popen("timeout 60 neutron port-list | grep 'existing\|new' | awk \'{print $2}\' 2> /dev/null")
output = f.read()
output = output.splitlines()
for i in output:
    try:
        # neutron.delete_port(i)
        os.system("neutron port-delete " + i + " &> /dev/null")
        time.sleep(0.5)
    except:
        pass

f = os.popen("timeout 60 neutron subnet-list | grep new | awk \'{print $2}\' 2> /dev/null")
output = f.read()
output = output.splitlines()
for i in output:
    try:
        # neutron.delete_subnet(i)
        os.system("neutron subnet-delete " + i + " &> /dev/null")
        time.sleep(0.5)
    except:
        pass

f = os.popen("timeout 60 neutron net-list | grep new | awk \'{print $2}\' 2> /dev/null")
output = f.read()
output = output.splitlines()
for i in output:
    try:
        # neutron.delete_network(i)
        os.system("neutron net-delete " + i + " &> /dev/null")
        time.sleep(0.5)
    except:
        pass

def parse_logfiles():
    min_delay = 0.0
    avg_delay = 0.0
    max_delay = 0.0
    total_drop = 0
    total_sent = 0
    total_received = 0
    drop_percentage = 0.0

    f = os.popen("ls testns-DHCP-network*")
    output = f.read()
    output = output.splitlines()
    number_of_logfiles = len(output)

    for logfile in output:
        f = os.popen("grep \"drops:\" " + logfile + " | awk \'{print $2}\' 2> /dev/null")
        output = f.read()
        output = output.splitlines()

        if len(output) == 0:
            print "\n  ERROR: {0} has errors. Cannot find drops\n".format(logfile)
            continue
  
        for o in output:
            total_drop = total_drop + int(o)

        f = os.popen("grep sent " + logfile + " | awk \'{print $3}\' 2> /dev/null")
        output = f.read()
        output = output.splitlines()
 
        if len(output) == 0:
            print "\n  ERROR: {0} has errors. Cannot find number of sent packets\n".format(logfile)
            continue

        for o in output:
            total_sent = total_sent + int(o)

        f = os.popen("grep received " + logfile + " | awk \'{print $3}\' 2> /dev/null")
        output = f.read()
        output = output.splitlines()

        if len(output) == 0:
            print "\n  ERROR: {0} has errors. Cannot find number of received packets\n".format(logfile)
            continue

        for o in output:
            if o.isdigit():
                total_received = total_received + int(o)

        drop_percentage = drop_percentage + ((100.00 * float(total_drop)) / float(total_sent))

        f = os.popen("grep min " + logfile + " | awk \'{print $3}\' 2> /dev/null")
        output = f.read()
        output = output.splitlines()

        if len(output) < 2:
            print "\n  ERROR: {0} has errors. Cannot find min_delay\n".format(logfile)
            continue

        min_delay = min_delay + float(output[0]) + float(output[1])

        f = os.popen("grep avg " + logfile + " | awk \'{print $3}\' 2> /dev/null")
        output = f.read()
        output = output.splitlines()

        if len(output) < 2:
            print "\n  ERROR: {0} has errors. Cannot find avg_delay\n".format(logfile)
            continue

        avg_delay = avg_delay + float(output[0]) + float(output[1])

        f = os.popen("grep max " + logfile + " | awk \'{print $3}\' 2> /dev/null")
        output = f.read()
        output = output.splitlines()

        if len(output) < 2:
            print "\n  ERROR: {0} has errors. Cannot find max_delay\n".format(logfile)
            continue

        max_delay = max_delay + float(output[0]) + float(output[1])

    # Total number of packets sent in all logfiles
    print "Total number of packets sent     = {0}".format(total_sent)

    # Total number of packets received in all logfiles
    print "Total number of packets received = {0}".format(total_received)

    # Total number of packets dropped in all logfiles
    print "Total number of packets dropped  = {0}".format(total_drop)

    # Find average drop_percentage in all logfiles
    drop_percentage = drop_percentage / float(number_of_logfiles)
    print "Packet drop % = {0} %".format(drop_percentage)
 
    # Find average min_delay in all logfiles
    min_delay = min_delay / float(number_of_logfiles)
    print "Minimum time to receive DHCP IP address = {0} milliseconds".format(min_delay)

    # Find average avg_delay in all logfiles
    avg_delay = avg_delay / float(number_of_logfiles)
    print "Average time to receive DHCP IP address = {0} milliseconds".format(avg_delay)

    # Find average max_delay in all logfiles
    max_delay = max_delay / float(number_of_logfiles)
    print "Maximum time to receive DHCP IP address = {0} milliseconds".format(max_delay)

# Parse all logfiles and find minimum, average and maximum time needed to
# receive DHCP IP address
parse_logfiles()

print "\nThe CPU and memory usage numbers are saved in the file\n"\
"{0} in the current directory".format(cpu_filename)

f = os.popen("tail -5 " + cpu_filename)
output = f.read()
output = output.splitlines()
for line in output:
    print line

# Copy logfiles to perfdhcp_logs directory
if not os.path.isdir("perfdhcp_logs"):
    os.mkdir("perfdhcp_logs")

# Save logs only for port-scaling and not for network-scaling as
# there will be too many logs during network-scaling (one log file
# is generated for each network)

if dhcp_network_count == 1:
    f = os.popen("mv *.log perfdhcp_logs")
    output = f.read()
    output = output.splitlines()

os.system("rm -rf testns*.log")
os.system("rm -rf *memory*.log")

print ""
