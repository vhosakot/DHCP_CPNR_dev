rpm -e openstack-cisco-cpnrdhcp-driver-2014.1.2.1-2.el7.centos.noarch
rm -rf /usr/lib/python2.7/site-packages/neutron/plugins/cisco/cpnr/
rm -rf /usr/bin/neutron-dhcp-relay
rm -rf /usr/bin/neutron-dns-relay
rm -rf /var/log/neutron/*relay*
rm -rf /var/log/neutron/*.gz
cd /root/DHCP_CPNR_dev/CPNR_RPM/mock/CPNR_source/
rm -rf *.rpm *.log
rm -rf cisco-cpnrdhcp-driver-2014.1.2.1/.eggs/
rm -rf cisco-cpnrdhcp-driver-2014.1.2.1/*egg*
ls -lrta cisco-cpnrdhcp-driver-2014.1.2.1
ls -lrta
cd /root/DHCP_CPNR_dev/CPNR_RPM/mock/CPNR_source/
