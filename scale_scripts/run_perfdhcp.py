#! /usr/bin/python

import os
import time
import thread

os.system("rm -rf *.log")

# Clear neutron logs
os.system("rm -rf /var/log/neutron/*.gz")
os.system("rm -rf /var/log/neutron/*metadata*.log")
os.system("> /var/log/neutron/dhcp-agent.log")
os.system("> /var/log/neutron/server.log")
os.system("> /var/log/neutron/openvswitch-agent.log")
os.system("> /var/log/neutron/dnsmasq.log")

f = os.popen("neutron net-list | grep DHCP | wc -l 2> /dev/null")
output = f.read()
output = output.splitlines()
dhcp_network_count = int(output[0])

f = os.popen("neutron port-list | grep DHCP | wc -l 2> /dev/null")
output = f.read()
output = output.splitlines()
dhcp_ports = int(output[0])
dhcp_ports_per_network = dhcp_ports / dhcp_network_count

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
                os.system("> /var/log/neutron/dhcp-agent.log")
                os.system("> /var/log/neutron/server.log")
                os.system("> /var/log/neutron/openvswitch-agent.log")
                os.system("> /var/log/neutron/dnsmasq.log")
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

# Start measuring CPU and memory usage in a separate thread before running perfdhcp
thread.start_new_thread(measure_cpu_memory, ())

# Start port churn and network churn in a separate thread before running perfdhcp

for i in range(0, dhcp_network_count):
    testns = "testns-DHCP-network-" + str(i)
    logfile = testns + "_" + str(dhcp_ports_per_network) + "_" + time.strftime("%m%d%Y_%H%M%S") + ".log"
    cmd = "sudo ip netns exec " + testns + " ip a | grep tap"
    f = os.popen(cmd)
    output = f.read()
    output = output.splitlines()
    test_tap_interface = output[0].split()[1].split(':')[0]

    cmd = "sudo ip netns exec " + testns + " /usr/local/sbin/perfdhcp -4 -b mac=fa:16:00:00:00:00 -r " + str(dhcp_ports_per_network) + " -R " + str(dhcp_ports_per_network) + " -n " + str(dhcp_ports_per_network) + " -l " + test_tap_interface + " &> " + logfile + " &"
    print cmd
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

# Wait for measure_cpu_memory running in a separate thread to stop
time.sleep(5)

# Wait for port churn and network churn running in a separate thread to stop
os.system("sudo pkill -f port_network_churn.py")
time.sleep(2)
os.system("sudo pkill -f port_network_churn.py")
time.sleep(2)
os.system("./port_network_churn.py -delete")
time.sleep(2)
os.system("./port_network_churn.py -delete")

def parse_logfiles():
    min_delay = 0.0
    avg_delay = 0.0
    max_delay = 0.0

    f = os.popen("ls testns-DHCP-network*")
    output = f.read()
    output = output.splitlines()
    number_of_logfiles = len(output)

    for logfile in output:
        f = os.popen("grep \"drops:\" " + logfile + " | awk \'{print $2}\' 2> /dev/null")
        output = f.read()
        output = output.splitlines()

        if output == []:
            print "\n  ERROR: {0} has errors.\n".format(logfile)
            continue

        if (output[0] == "0" and output[1] == "0"):
            # No packets were dropped
            pass
        else:
            print "\n================================"
            print "\n  ERROR: {0} has dropped packets.\n".format(logfile)
            os.system("cat " + logfile)
            print "\n================================\n"

        f = os.popen("grep -A 10 REQUEST-ACK " + logfile + " | grep min | awk \'{print $3}\' 2> /dev/null")
        output = f.read()
        output = output.splitlines()
        min_delay = min_delay + float(output[0])

        f = os.popen("grep -A 10 REQUEST-ACK " + logfile + " | grep avg | awk \'{print $3}\' 2> /dev/null")
        output = f.read()
        output = output.splitlines()
        avg_delay = avg_delay + float(output[0])

        f = os.popen("grep -A 10 REQUEST-ACK " + logfile + " | grep max | awk \'{print $3}\' 2> /dev/null")
        output = f.read()
        output = output.splitlines()
        max_delay = max_delay + float(output[0])

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

# os.system("rm -rf *.log")

print ""
