#! /usr/bin/python

import os
import sys
import time
import thread
from neutronclient.v2_0 import client as neutron_client

def get_neutron_credentials():
    d = {}
    d['username'] = os.environ['OS_USERNAME']
    d['password'] = os.environ['OS_PASSWORD']
    d['auth_url'] = os.environ['OS_AUTH_URL']
    d['tenant_name'] = os.environ['OS_TENANT_NAME']
    return d

neutron_credentials = get_neutron_credentials()
neutron = neutron_client.Client(**neutron_credentials)
network_list = neutron.list_networks()
DHCP_network_count = len(network_list['networks']) - 1

script_ended = False
cpu_filename = ""
slept_secs = 0

def delete_churn_ports():
    global neutron_credentials
    global neutron

    ports = neutron.list_ports()['ports']
    for port in ports:
        if "churn" in port['name']:
            try:
                neutron.delete_port(port['id'])
            except:
                pass
    while len(neutron.list_ports()['ports']) != DHCP_port_count:
        time.sleep(2)

def measure_cpu_memory():
    try:
        global script_ended
        global cpu_filename
        global slept_secs
        cpu_filename = "dhcp_scale_cpu_memory_" + time.strftime("%m%d%Y_%H%M%S") + '.log'
        cpu_mem_file = open(cpu_filename, 'w')
        neutron_server_cpu_mem_dict = {'pid':"", 'cpu':[], 'memory':[]}
        neutron_dhcp_agent_cpu_mem_dict = {'pid':"", 'cpu':[], 'memory':[]}
        system_memory_list = []
        system_cpu_list = []
    
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
    
            f = os.popen("cat /proc/meminfo | grep -i Memfree | awk \'{print $2}\'")
            out = f.read()
            system_memory_list.append(out.splitlines()[0])
    
            f = os.popen("top -b -n 3 -d 1 | grep Cpu | tail -n 1 | awk \'{print 100 - $8}\'")
            out = f.read()
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
                slept_secs = 0
    
        avg_neutron_server_cpu = 0
        avg_neutron_server_mem = 0
        avg_dhcp_agent_cpu = 0
        avg_dhcp_agent_mem = 0
    
        cpu_mem_file.write("********\nneutron-server (PID " + neutron_server_cpu_mem_dict['pid'] + ")\n")
        cpu_mem_file.write("**********************\n")
        cpu_mem_file.write("CPU usage percentage (cputime/realtime ratio)\n")
        cpu_mem_file.write("----------------\n")
        for cpu in neutron_server_cpu_mem_dict['cpu']:
            avg_neutron_server_cpu = avg_neutron_server_cpu + float(cpu)
            cpu_mem_file.write(cpu + "\n")
        cpu_mem_file.write("Memory usage in kB\n")
        cpu_mem_file.write("----------------\n")
        for mem in neutron_server_cpu_mem_dict['memory']:
            avg_neutron_server_mem = avg_neutron_server_mem + float(mem)
            cpu_mem_file.write(str(mem) + "\n")
    
        avg_neutron_server_cpu = avg_neutron_server_cpu / len(neutron_server_cpu_mem_dict['cpu'])
        avg_neutron_server_mem = avg_neutron_server_mem / len(neutron_server_cpu_mem_dict['memory'])
    
        cpu_mem_file.write("\n\n********\nneutron-dhcp-agent (PID " + neutron_dhcp_agent_cpu_mem_dict['pid'] + ")\n")
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
        cpu_mem_file.write("\n\n********\nTotal system memory free in kB (cat /proc/meminfo | grep -i Memfree)\n")
        cpu_mem_file.write("**********************\n")
        for sys_mem in system_memory_list:
            avg_system_mem_free = avg_system_mem_free + float(sys_mem)
            cpu_mem_file.write(sys_mem + "\n")
    
        avg_system_mem_free = avg_system_mem_free / len(system_memory_list)
    
        avg_system_cpu_used = 0
        cpu_mem_file.write("\n\n********\nTotal system CPU used % (top -b -n 3 -d 1 | grep Cpu | tail -n 1 | awk \'{print 100 - $8}\')\n")
        cpu_mem_file.write("**********************\n")
        for sys_cpu in system_cpu_list:
            avg_system_cpu_used = avg_system_cpu_used + float(sys_cpu)
            cpu_mem_file.write(sys_cpu + "\n")
    
        avg_system_cpu_used = avg_system_cpu_used / len(system_cpu_list)
    
        cpu_mem_file.write("\n\nneutron-server average CPU usage        = " + str(avg_neutron_server_cpu) + " %\n")
        cpu_mem_file.write("neutron-server average memory usage     = " + str(avg_neutron_server_mem) + " kB\n")
        cpu_mem_file.write("neutron-dhcp-agent average CPU usage    = " + str(avg_dhcp_agent_cpu) + " %\n")
        cpu_mem_file.write("neutron-dhcp-agent average memory usage = " + str(avg_dhcp_agent_mem) + " kB\n")
        cpu_mem_file.write("Average total system memory free        = " + str(avg_system_mem_free) + " kB\n")
        cpu_mem_file.write("Average total system CPU used %         = " + str(avg_system_cpu_used) + " %\n")
    
        cpu_mem_file.close()
    except:
        cpu_mem_file.close()
        return

a = 0
b = 0
os.system("rm -rf run_test.sh")
filename = "run_test.sh"
run_test_file = open(filename, 'w')
run_test_file.write("rm -rf *DHCP*.log\n")

DHCP_network_count = len(neutron.list_networks()['networks']) - 1
DHCP_port_count = len(neutron.list_ports()['ports'])
DHCP_ports_per_network = DHCP_port_count / DHCP_network_count
DHCP_ports_per_network = DHCP_ports_per_network - 3

for i in range(0, DHCP_network_count):
    network_name = "DHCP-network-" + str(i)
    network_id = neutron.list_networks(name=network_name)['networks'][0]['id']

    print "\nChecking namespace {0} before starting test\n".format("qdhcp-" + network_id)
    cmd = "sudo ip netns exec qdhcp-" + network_id + " ip a"
    print cmd
    f = os.popen(cmd)
    output = f.read().splitlines()
    for line in output:
        print line

    print "\novs-vsctl show"
    f = os.popen("ovs-vsctl show")
    output = f.read().splitlines()
    for line in output:
        print line

    cmd = "sudo ip netns exec qdhcp-" + network_id + " ip a | grep 169.254.169.254"
    f = os.popen(cmd)
    f_list = f.read().splitlines()
    if f_list == []:
        raise Exception("\n\nDHCP server NOT found in namespace. Exiting...\n\n")
        sys.exit(0)
    output = f_list[0]
    metadata_tap_interface = output.split()[len(output.split()) - 1]

    cmd = "sudo ip netns exec qdhcp-" + network_id + " ip a | grep state | grep tap | grep -v " + metadata_tap_interface
    f = os.popen(cmd)
    output = f.read()
    test_tap_interface = output.splitlines()[0].split(" ")[1][:-1]
    print "\ntest_tap_interface = {0}".format(test_tap_interface)

    spoof_start_mac_address = "de:ae:" + '{0:x}'.format(int(a)) + '{0:x}'.format(int(b)) + ":00:00:00"
    if '{0:x}'.format(int(b)) == 'f':
        if '{0:x}'.format(int(a)) == 'f':
            print "\n  ERROR : Cannot spoof anymore MAC addresses\n"
            delete_churn_ports()
            sys.exit(0)
        a = a + 1
        b = 0
    else:
        b = b + 1

    cmd = "sudo ip netns exec qdhcp-" + network_id + " python ./dhcp.py -m " + spoof_start_mac_address + " -c " + str(DHCP_ports_per_network) + " -i " + test_tap_interface + " -R " + str(DHCP_ports_per_network) + " -D -d &> " + network_name + ".log &\n"
    run_test_file.write(cmd)

run_test_file.close()
os.system("chmod 777 run_test.sh")

time.sleep(5)

os.system("systemctl restart neutron-dhcp-agent.service")
print "\nWaiting 60 seconds after restarting neutron-dhcp-agent.service...\n"
time.sleep(60)
os.system("systemctl status neutron-dhcp-agent.service | grep since")
print "  "

dhcp_network_churn_ports_dict = {}
churn_ports_per_network = 2
churn_sleep_time = 60
sleep_between_threads = 0.1

if len(sys.argv) >= 2 and sys.argv[1].isdigit():
    churn_ports_per_network = int(sys.argv[1])

if len(sys.argv) == 3 and sys.argv[2].isdigit():
    churn_sleep_time = int(sys.argv[2])

def create_port(net_id, j):
    global neutron_credentials
    global dhcp_network_churn_ports_dict

    port_name = "churn-port-" + str(j)
    json = {'port': {
        'admin_state_up': True,
        'name': port_name,
        'network_id': net_id}}

    neutron_t = neutron_client.Client(**neutron_credentials)
    churn_port = neutron_t.create_port(body=json)
    dhcp_network_churn_ports_dict[net_id].append(churn_port['port']['id'])

def delete_port(port_id):
    global neutron_credentials

    neutron_t = neutron_client.Client(**neutron_credentials)
    try:
        neutron_t.delete_port(port_id)
    except:
        pass

def churn():
    global DHCP_network_count
    global dhcp_network_churn_ports_dict
    global churn_ports_per_network
    global sleep_between_threads
    global churn_sleep_time
    global script_ended

    while script_ended is False:
        dhcp_network_churn_ports_dict = {}

        for i in range(0, DHCP_network_count):
            network_name = "DHCP-network-" + str(i)
            network_id = neutron.list_networks(name=network_name)['networks'][0]['id']
            dhcp_network_churn_ports_dict[network_id] = []

            # Create ports
            for j in range(0, churn_ports_per_network):
                time.sleep(sleep_between_threads)
                thread.start_new_thread(create_port, (network_id, j))

        # Sleep 60 seconds after creating ports so the 'hosts' file of dnsmasq
        # is updated and dnsmasq reloads
        time.sleep(60)

        for key,val in dhcp_network_churn_ports_dict.items():
            # Delete ports
            for churn_port in val:
                time.sleep(sleep_between_threads)
                thread.start_new_thread(delete_port, (churn_port,))

        dhcp_network_churn_ports_dict = {}

        # Sleep 30 seconds after deleting ports so the 'hosts' file of dnsmasq
        # is updated and dnsmasq reloads
        time.sleep(30)

        time.sleep(churn_sleep_time)

os.system("rm -rf /var/log/neutron/*.gz")
os.system("rm -rf /var/log/neutron/*metadata*.log")
os.system("> /var/log/neutron/dhcp-agent.log")
os.system("> /var/log/neutron/server.log")
os.system("> /var/log/neutron/openvswitch-agent.log")

# Measure CPU and memory usage every second in a different thread
thread.start_new_thread(measure_cpu_memory, ())

# Start port-churn is a separate thread
thread.start_new_thread(churn, ())

os.system("./run_test.sh")
start = time.time()

while 1:
    f = os.popen("ps aux | grep dhcp.py | grep -v grep | wc -l")
    output = f.read()
    process_count = output.splitlines()[0]
    if process_count == '0':
        script_ended = True
        print "Done!"
        break
    else:
        end = time.time()
        if (end-start) > 7200:
            script_ended = True
            print " \nERROR : All the processes did not end. {0} processes still running. "\
            "Waited 120 minutes. Exiting...\n".format(process_count)
            #print " Run \'ps aux | grep dhcp.py | grep -v grep\'\n"
            #print " Run \'sudo pkill -f ./dhcp.py\' to kill all processes\n"
            os.system("sudo pkill -f dhcp.py")
            os.system("sudo pkill -f dhcp_entries.py")
            time.sleep(10)
            log_name = logfile.split(".")[0] + "_" + str(DHCP_network_count) + "_" + str(DHCP_ports_per_network) + "_" + time.strftime("%m%d%Y_%H%M%S") + ".log"
            cmd = "cp " + logfile + " /root/DHCP_CPNR_dev/DHCP_error_logs/" + log_name
            os.system(cmd)
            delete_churn_ports()
            sys.exit(0)
        else:
            time.sleep(5)
            print "{0} processes still running. Waited {1} seconds.".format(process_count, end-start)

avg_offer_delay = 0
avg_ack_delay = 0
total_dhcp_discovers_sent = 0
dhcp_time_list = []
f = os.popen("ls *DHCP*.log")
output = f.read()
logfile_list = output.splitlines()
print "Discover Sent    Offer Received    Request Sent    Ack Received    Avg Offer Delay           Avg Ack Delay"
for logfile in logfile_list:
    cmd = "grep -A 2 \"Avg Ack Delay\" " + logfile + " | grep -v \"\-\-\-\""
    f = os.popen(cmd)
    output = f.read()
    if output.splitlines() == []:
        print "\n ERROR 1 : {0} has invalid data.\n".format(logfile)
        log_name = logfile.split(".")[0] + "_" + str(DHCP_network_count) + "_" + str(DHCP_ports_per_network) + "_" + time.strftime("%m%d%Y_%H%M%S") + ".log"
        cmd = "cp " + logfile + " /root/DHCP_CPNR_dev/DHCP_error_logs/" + log_name
        os.system(cmd)
        delete_churn_ports()
        sys.exit(0)
    try:
        output = output.splitlines()[1].split()
        output.pop(4)
        output.pop(4)
        avg_offer_delay = avg_offer_delay + float(output[4])
        avg_ack_delay = avg_ack_delay + float(output[5])
        total_dhcp_discovers_sent = total_dhcp_discovers_sent + int(output[0])
    except:
            print "\n ERROR 1.1 : {0} has invalid data.\n".format(logfile)
            log_name = logfile.split(".")[0] + "_" + str(DHCP_network_count) + "_" + str(DHCP_ports_per_network) + "_" + time.strftime("%m%d%Y_%H%M%S") + ".log"
            cmd = "cp " + logfile + " /root/DHCP_CPNR_dev/DHCP_error_logs/" + log_name
            os.system(cmd)
            delete_churn_ports()
            sys.exit(0)
    output = "               ".join(output)
    print "{0}     {1}".format(output, logfile)

    cmd = "grep -A " + str(DHCP_ports_per_network + 1) + " MAC " + logfile
    f = os.popen(cmd)
    output = f.read()
    if output.splitlines() == []:
        print "\n ERROR 2 : {0} has invalid data.\n".format(logfile)
        log_name = logfile.split(".")[0] + "_" + str(DHCP_network_count) + "_" + str(DHCP_ports_per_network) + "_" + time.strftime("%m%d%Y_%H%M%S") + ".log"
        cmd = "cp " + logfile + " /root/DHCP_CPNR_dev/DHCP_error_logs/" + log_name
        os.system(cmd)
        delete_churn_ports()
        sys.exit(0)
    output = output.splitlines()
    for line in output:
        if "MAC" in line or "--" in line:
            continue
        line = line.split()
        try:
            float(line[8])
            float(line[9])
        except:
            continue
            #print "\n ERROR 3 : {0} has invalid data.\n".format(logfile)
            #sys.exit(0)
        dhcp_time_list.append(float(line[8]) + float(line[9]))
    
#print "\nAverage DHCP Offer delay = {0} seconds".format(avg_offer_delay/DHCP_network_count)
#print "Average DHCP Ack delay   = {0} seconds".format(avg_ack_delay/DHCP_network_count)
print "\nAverage time needed to receive DHCP IP  = {0} seconds".format(avg_offer_delay/DHCP_network_count + avg_ack_delay/DHCP_network_count)

# Sleep for 3 seconds so the other thread running measure_cpu_memory ends
time.sleep(3)

delete_churn_ports()

print "The CPU and memory usage numbers are saved in the file\n"\
" {0} in the current directory\n".format(cpu_filename)

dhcp_time_list.sort()
print "Min time needed to receive DHCP IP    = {0} seconds".format(dhcp_time_list[0])
print "Median time needed to receive DHCP IP = {0} seconds".format(dhcp_time_list[len(dhcp_time_list) / 2])
print "Max time needed to receive DHCP IP    = {0} seconds".format(dhcp_time_list[len(dhcp_time_list) - 1])
print "Total number of DHCPDISCOVER retries  = {0}\n".format(total_dhcp_discovers_sent)

cmd = "tail -6 " + cpu_filename
os.system(cmd)
