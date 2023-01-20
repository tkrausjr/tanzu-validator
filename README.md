# tanzu-validator
tz-validate can be run to quickly validate a vSphere with Tanzu environment is ready and healthy. 

## Use Cases 
- New deployment of a site - Validate Tanzu environment is ready to go
- After power outage or periodically to check environment readiness.
- Quickly check a site or all sites for Software versions used for ALB, VC, SC, ESXi

## Test Coverage
For updated test coverage, see the Test_Coverage.md document in the docs folder of this repo.

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
ALB_IP: '192.168.100.163'
ALB_USER: 'admin'
ALB_PW: '***********'


``` 

## 2- Run the Validation
You have two options for running the environment prechecks. Both options require you to create the **test_params.yaml** file in the $HOME directory of the linux machine where you will either run the script (locally or via Docker container). You should copy paste the sample **test_params.yaml** file from this repo into your $HOME directory as a starting point and update the values for the environment being tested.

### Option 2a(Preferred) - Run from a Docker Container on a host with Docker and access to VM Management Network

On any nix machine with Docker already installed.
```
docker run -it --rm -v $HOME:/root -w /usr/src/app mytkrausjr/py3-tz-validate:v7 python tz-validate.py -n vsphere
```
**NOTE:** On systems with SELinux enabled you need to pass an extra mount option "z" to the end of the volume definition in docker run. Without this option you will get a permission error when you run the container.
```
docker run -it --rm -v $HOME:/root:z -w /usr/src/app mytkrausjr/py3-tz-validate:v7 python tz-validate.py -n vsphere
```

### Option 2b - Run script locally on Linux machine with access to VM Management Network

On Ubuntu 18.04 with Python3 already installed.
```
git clone https://github.com/tkrausjr/tanzu-validator.git
cd tanzu-validator/
chmod +x ./wcp_tests.py 
cp ./test_params.yaml ~/tz-validate-params.yaml
vi ~/tz-validate-params.yaml    ### See Below of explanation
pip3 install pyVmomi
pip3 install pyaml
pip3 install requests
pip3 install pyVim
```

To run the validation script
``` bash

❯ ./tz-validate.py -h                              
usage: tz-validate.py [-h] [--version] [-m {version-checks,validation}] [-v [{INFO,DEBUG}]]

tz-validate.py validates environments for healthy Supervisor Clusters
setup in vSphere 7 with Tanzu. Uses YAML configuration files to specify
environment information to test. Find additional information at:
(https://github.com/tkrausjr/tanzu-validator.git)

optional arguments:
  -h, --help            show this help message and exit
  --version             show programs version number and exit
  -m {version-checks,validation}, --mode {version-checks,validation}
                        Networking Environment(nsxt, vsphere)
  -v [{INFO,DEBUG}], --verbosity [{INFO,DEBUG}]

❯  ./tz-validate.py -m validation ~/tz-validate-params.yaml
