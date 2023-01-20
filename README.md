# tanzu-validator
WCP-Precheck project aims to make POC's and vSphere with Tanzu installations less painful for customers and overall more successful by quickly indentifying common misconfigurations and errors that would prevent a successful installation of WCP .  The pre-checks can be run by VMware Tanzu SE's or Customers to quickly validate a vSphere environment is ready for a successful vSphere with Tanzu Supervisor Cluster creation.  The project has options for testing both NSX-T based and vSphere based networking for vSphere with Tanzu and can be run as a standalone script or via Docker.

## Test Coverage
For updated test coverage, see the Test_Coverage.md document in this repo.

## 1 - Create and Populate the Parameters file used for input values 
Download the sample parameters file from this repo or copy and paste below to a parameters file named **test_params.yaml** in the $HOME folder on the system where you will run the validation script.
``` yaml
### COMMON SETTINGS
DOMAIN: 'tpmlab.vmware.com'
NTP_SERVER: 'time.vmware.com'
DNS_SERVERS:
  - '10.173.13.90'
VC_HOST: 'vcsa.tpmlab.vmware.com'    # VCSA FQDN or IP MUST ADD A Rec to DNS
VC_IP: '10.173.13.81'                      # VCSA IP
VC_SSO_USER: 'administrator@vsphere.local'
VC_SSO_PWD:  '***********'
VC_DATACENTER: 'Datacenter'
VC_CLUSTER:  'Nested-TKG-Cluster'    # VSphere HA/DRS Cluster created for Tanzu Supervisor Cluster
VC_STORAGEPOLICIES:          # VM Storage Policies created for Tanzu
  - 'thin'  
  - 'thinner'      

### Section for vSphere Networking Deployments
VDS_NAME: 'vds-1'
VDS_MGMT_PG: 'management-vm'  # Management for Supervisor Cluster and HAProxy Mgmt Interface
VDS_PRIMARY_WKLD_PG: 'not_there'  # Combined PG for Workload Network and HAProxy VIP Network
HAPROXY_IP: '192.168.100.163'
HAPROXY_PORT: 5556      # HAProxy Dataplane API Mgmt Port chosen during OVA Deployment
HAPROXY_IP_RANGE_START: '10.173.13.38' # HAProxy LB IP Range chosen during OVA Deployment
HAPROXY_IP_RANGE_SIZE: 29
HAPROXY_USER: 'admin'
HAPROXY_PW: '***********'

### Section for NSX-T Networking Deployments
VDS_NAME: 'vds-1'
VDS_MGMT_PG: 'management-vm'
VDS_UPLINK_PG: 'ext-uplink-edge'
VDS_EDGE_TEP_PG: 'tep-edge'
HOST_TEP_VLAN: 102
NSX_MGR_HOST: 'nsxmgr.tpmlab.vmware.com'   # FQDN of NSX-T Manager Appliance
NSX_MGR_IP: '10.173.13.82'    # IP Addr of NSX-T Manager Appliance
NSX_USER: 'admin'   # API Username for NSX-T Manager Appliance
NSX_PASSWORD: '***********'    # API Password for NSX-T Manager Appliance

### Section for WCP Supervisor Cluster Deployment
WCP_MGMT_STARTINGIP: '192.168.100.141'  # 1st IP of 5 consecutive needed for S.C. on Mgmt net
WCP_MGMT_MASK: '255.255.255.0'
WCP_MGMT_GATEWAY: '192.168.100.1'


``` 

## 2- Run the Pre-checks
You have two options for running the environment prechecks. Both options require you to create the **test_params.yaml** file in the $HOME directory of the linux machine where you will either run the script (locally or via Docker container). You should copy paste the sample **test_params.yaml** file from this repo into your $HOME directory as a starting point and update the values for the environment being tested.

### Option 2a(Preferred) - Run from a Docker Container on a host with Docker and access to VM Management Network

On any nix machine with Docker already installed.
```
docker run -it --rm -v $HOME:/root -w /usr/src/app mytkrausjr/py3-wcp-precheck:v7 python wcp_tests.py -n vsphere
```
**NOTE:** On systems with SELinux enabled you need to pass an extra mount option "z" to the end of the volume definition in docker run. Without this option you will get a permission error when you run the container.
```
docker run -it --rm -v $HOME:/root:z -w /usr/src/app mytkrausjr/py3-wcp-precheck:v7 python wcp_tests.py -n vsphere
```

### Option 2b - Run script locally on Linux machine with access to VM Management Network

On Ubuntu 18.04 with Python3 already installed.
```
git clone https://gitlab.eng.vmware.com/TKGS-TSL/wcp-precheck.git              
Cloning into 'wcp-precheck'...
Username for 'https://gitlab.eng.vmware.com':   <VMware User ID IE njones>
Password for 'https://kraust@gitlab.eng.vmware.com':  <VMware Password>
cd wcp-precheck/pyvim
chmod +x ./wcp_tests.py 
cp ./test_params.yaml ~/test_params.yaml
vi ~/test_params.yaml    ### See Below of explanation
pip3 install pyVmomi
pip3 install pyaml
pip3 install requests
pip3 install pyVim
```


To run the validation script
``` bash

❯ cd github/wcp-precheck/pyvim
❯ ./wcp_tests.py -h                              
usage: wcp_tests.py [-h] [--version] [-n {nsxt,vsphere}] [-v [{INFO,DEBUG}]]

vcenter_checks.py validates environments for succcesful Supervisor Clusters
setup in vSphere 7 with Tanzu. Uses YAML configuration files to specify
environment information to test. Find additional information at:
gitlab.eng.vmware.com:TKGS-TSL/wcp-precheck.git

optional arguments:
  -h, --help            show this help message and exit
  --version             show programs version number and exit
  -n {nsxt,vsphere}, --networking {nsxt,vsphere}
                        Networking Environment(nsxt, vsphere)
  -v [{INFO,DEBUG}], --verbosity [{INFO,DEBUG}]

❯ wcp_tests.py -n nsxt 
