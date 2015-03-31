service nwreglocal stop
service nwregregion stop
sleep 1
./cpnr_8_3/Linux5/uninstall_cnr
sleep 1
rm -rf /opt/nwreg2
rm -rf /var/nwreg2
sudo yum -y remove glibc.i686
sudo yum -y remove glibc-common
sudo yum -y remove libstdc++.i686
sudo yum -y remove compat-libstdc++-33.i686
sudo yum -y remove cyrus-sasl-lib.i686
sudo yum -y remove unzip
sudo yum -y remove wget
rm -rf jre-7u67-linux-i586.rpm*
sudo rpm -e jre-1.7.0_67-fcs.i586
rm -rf cpnr_8_3*
rm -rf *.ini
rm -rf *.lic
