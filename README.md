# tanzu-validator
tz-validate.py can be run to quickly validate a vSphere with Tanzu environment is ready and healthy. 

## Use Cases 
- New deployment of a site - Validate Tanzu environment is ready to go.
- After power outage or periodically to check environment readiness.
- Quickly check a site or all sites for Software versions used for ALB, VC, SC, and ESXi

## Test Coverage
For updated test coverage, see the [Test_Coverage.md](https://github.com/tkrausjr/tanzu-validator/blob/main/docs/Test_Coverage.md) document in the docs folder of this repo.

## 1 - Create and Populate the Parameters file used for input values 
Download the sample parameters file from this repo or copy and paste below to a parameters file on the system where you will run the validation script.
``` yaml
### COMMON SETTINGS
DOMAIN: 'tpmlab.domain.com'
NTP_SERVER: 'time.domain.com'
DNS_SERVERS:
  - '10.19.22.90'
VC_HOST: 'vcsa.tpmlab.domain.com'    # VCSA FQDN or IP MUST ADD A Rec to DNS
VC_IP: '10.19.22.81'                      # VCSA IP
VC_SSO_USER: 'administrator@vsphere.local'
VC_SSO_PWD: '**********'
VC_DATACENTER: 'Datacenter'
VC_CLUSTER:  'Nested-TKG-Cluster'
VC_STORAGEPOLICIES:          # Storage Policies to use 
  - 'thin'  
  - 'thinner'      
VC_DATASTORE: '66-datastore3'    # Validate existence of proper datastores

### Section for vSphere Networking Deployments
VDS_NAME: 'vds-1'
VDS_MGMT_PG: 'management-vm'
VDS_PRIMARY_WKLD_PG: 'not_there'
VDS_WKLD_PG: 'ext-uplink-edge'
ALB_CTLR_IP: '192.168.100.163'
ALB_CTLR_USER: 'admin'
ALB_CTLR_PW: '**********'
ALB_HEALTH_MIN: 75
``` 
## 2- Run the Validation
You have two options for running the environment prechecks. Both options require you to create the **test_params.yaml** file in the $HOME directory of the linux machine where you will either run the script (locally or via Docker container). You should copy paste the sample **test_params.yaml** file from this repo into your $HOME directory as a starting point and update the values for the environment being tested.


### Option 2a - Run script locally on Linux machine with access to VM Management Network

On Ubuntu 20.04 with Python3 already installed.
``` bash
git clone https://github.com/tkrausjr/tanzu-validator.git
cd tanzu-validator/
chmod +x ./tz-validate.py 
cp ./test_params.yaml ~/tz-validate-params.yaml
vi ~/tz-validate-params.yaml    ### See Above for explanation of values
python3 -m pip install requests
python3 -m pip install PyYAML
python3 -m pip install kubernetes
python3 -m pip install 'pyvmomi==7.0.3'


```
To get help with validation script
``` bash
python3 tz-validate.py -h
usage: tz-validate.py [-h] [--version] -f FILE [-v [{INFO,DEBUG}]]

vcenter_checks.py validates environments for succcesful Supervisor Clusters setup in vSphere 7 with Tanzu. Uses YAML configuration files to specify environment
information to test.

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -f FILE, --file FILE  (Required) Params YAML file
  -v [{INFO,DEBUG}], --verbosity [{INFO,DEBUG}]
```
To run the validation script
``` bash
python3 tz-validate.py -f /home/tkrausjr/test_params.yaml

python3 tz-validate.py -f /home/tkrausjr/test_params.yaml
INFO: 2023-03-15 23:22:06: __main__: 390: Workload Control Plane Network Type is vsphere 
INFO: 2023-03-15 23:22:06: __main__: 392: -- Checking Required YAML inputs for program: 
 
INFO: 2023-03-15 23:22:06: __main__: 399: ************ Beginning vCenter Environment Testing ************
INFO: 2023-03-15 23:22:06: __main__: 408: --vCenter TEST 2 - Checking vCenter IP is Active for vCenter
INFO: 2023-03-15 23:22:08: __main__: 87: ---- SUCCESS - Can ping 192.168.100.15. 
INFO: 2023-03-15 23:22:08: __main__: 410: --vCenter TEST 2 - Checking DNS Servers are reachable on network
INFO: 2023-03-15 23:22:10: __main__: 87: ---- SUCCESS - Can ping 10.173.13.90. 
INFO: 2023-03-15 23:22:10: __main__: 413: --vCenter TEST 2 - Checking Name Resolution for vCenter FQDN python-vcsa.tpmlab.vmware.com to IP 192.168.100.15
INFO: 2023-03-15 23:22:10: __main__: 74: ---- SUCCESS-The Hostname, python-vcsa.tpmlab.vmware.com resolves to the IP 192.168.100.15
ERROR: 2023-03-15 23:22:10: __main__: 77: ---- ERROR - Missing PTR Record. The IP, 192.168.100.15 does not resolve to the Hostname python-vcsa.tpmlab.vmware.com
INFO: 2023-03-15 23:22:10: __main__: 416: --vCenter TEST 3 - Checking VC is reachable via API using provided credentials
INFO: 2023-03-15 23:22:10: __main__: 97: ---- Trying to connect to VCENTER SERVER . . .
INFO: 2023-03-15 23:22:10: __main__: 99: ---- SUCCESS-Connected to vCenter VMware vCenter Server
INFO: 2023-03-15 23:22:11: __main__: 429: --vCenter TEST4 - Checking for the  Datacenter
INFO: 2023-03-15 23:22:11: __main__: 139: ---- SUCCESS - Managed Object Datacenter found.
INFO: 2023-03-15 23:22:11: __main__: 433: --vCenter TEST 5 - Checking for the Cluster
INFO: 2023-03-15 23:22:11: __main__: 151: ---- SUCCESS - Cluster Object pghv.ground.fedex.com found.
INFO: 2023-03-15 23:22:11: __main__: 439: --vCenter TEST 5a - Checking Hosts in the Cluster
ERROR: 2023-03-15 23:22:11: __main__: 164: ---- WARNING - ESXi Host 192.168.100.26 overall Status is yellow and not Green. Please correct any issues with this host.
ERROR: 2023-03-15 23:22:11: __main__: 164: ---- WARNING - ESXi Host 192.168.100.23 overall Status is yellow and not Green. Please correct any issues with this host.
ERROR: 2023-03-15 23:22:11: __main__: 164: ---- WARNING - ESXi Host 192.168.100.22 overall Status is yellow and not Green. Please correct any issues with this host.
ERROR: 2023-03-15 23:22:11: __main__: 164: ---- WARNING - ESXi Host 192.168.100.24 overall Status is yellow and not Green. Please correct any issues with this host.
ERROR: 2023-03-15 23:22:11: __main__: 164: ---- WARNING - ESXi Host 192.168.100.25 overall Status is yellow and not Green. Please correct any issues with this host.
INFO: 2023-03-15 23:22:11: __main__: 446: --vCenter TEST 6 - Getting Storage Policies from SPBM
INFO: 2023-03-15 23:22:11: __main__: 235: ---- SUCCESS - Found Storage Policy nfs-policy.
INFO: 2023-03-15 23:22:11: __main__: 235: ---- SUCCESS - Found Storage Policy vsan-policy.
INFO: 2023-03-15 23:22:11: __main__: 452: --vCenter TEST 7 - Checking Existence of the Datastores
INFO: 2023-03-15 23:22:11: __main__: 139: ---- SUCCESS - Managed Object vsanDatastore found.
INFO: 2023-03-15 23:22:11: __main__: 456: --vCenter TEST 8 - Checking for the vds
INFO: 2023-03-15 23:22:11: __main__: 139: ---- SUCCESS - Managed Object Dvswitch-01 found.
INFO: 2023-03-15 23:22:11: __main__: 460: --vCenter TEST 9 - Establishing REST session to VC API
INFO: 2023-03-15 23:22:11: __main__: 269: ---- SUCCESS - Successfully established session to VC 
INFO: 2023-03-15 23:22:11: __main__: 472: --vCenter TEST 11 - Checking time accuracy/synchronization in environment
INFO: 2023-03-15 23:22:11: __main__: 309: ---- vCenter 24hr time is 03:22:11
INFO: 2023-03-15 23:22:12: __main__: 484: ----------------------- Checking max time deltas on ESXi and vCenter hosts is less than 30
INFO: 2023-03-15 23:22:12: __main__: 182: ---- Lowest Time of all the Nodes is 1900-01-01 03:18:45.
INFO: 2023-03-15 23:22:12: __main__: 184: ---- Highest Time of all the Nodes is 1900-01-01 03:22:12.
INFO: 2023-03-15 23:22:12: __main__: 188: ---- Maximum allowable time drift is 0:00:30 seconds.
INFO: 2023-03-15 23:22:12: __main__: 189: ---- Largest Time delta between all nodes is 0:03:27 seconds.
ERROR: 2023-03-15 23:22:12: __main__: 195: ---- ERROR - Max Time Drift between all nodes is 0:03:27 which is higher than configured Max.
INFO: 2023-03-15 23:22:12: __main__: 488: --vCenter TEST 12 - Checking for existence and configuration of Content Library
INFO: 2023-03-15 23:22:12: __main__: 327: ---- SUCCESS - Found Content Library named local
INFO: 2023-03-15 23:22:12: __main__: 493: --vCenter TEST 13 - Checking Status of WCP Service on vCenter
INFO: 2023-03-15 23:22:12: __main__: 122: ---- SUCCESS-WCP Service Status STARTED
INFO: 2023-03-15 23:22:12: __main__: 123: ---- SUCCESS-WCP Service Health HEALTHY
INFO: 2023-03-15 23:22:12: __main__: 497: --vCenter TEST 16 - Checking for the Primary Workload Network PortGroup
INFO: 2023-03-15 23:22:12: __main__: 139: ---- SUCCESS - Managed Object Workload-Edge-VTEP-102 found.
INFO: 2023-03-15 23:22:12: __main__: 501: --vCenter TEST 17 - Checking for the Workload Network PortGroup
INFO: 2023-03-15 23:22:12: __main__: 139: ---- SUCCESS - Managed Object Workload-Edge-VTEP-102 found.
INFO: 2023-03-15 23:22:12: __main__: 505: --vCenter TEST 18 - Checking on cluster pghv.ground.fedex.com WCP Health
INFO: 2023-03-15 23:22:13: __main__: 343: ---- SUCCESS - vSphere w/ Tanzu status is RUNNING
INFO: 2023-03-15 23:22:13: __main__: 344: ---- SUCCESS - vSphere w/ Tanzu Supervisor Control Plane K8s API is RUNNING
INFO: 2023-03-15 23:22:13: __main__: 509: ************ Completed vCenter Environment Testing ************

INFO: 2023-03-15 23:22:13: __main__: 514: ************ Beginning AVI Environment Testing ************
INFO: 2023-03-15 23:22:13: __main__: 516: --AVI TEST 1 - Checking AVI Controller Health
INFO: 2023-03-15 23:22:13: __main__: 518: Avi controller 192.168.103.21 running version 20.1.7 has sessionid pj8hqreamigll3gq4pm3900xf769amlu
INFO: 2023-03-15 23:22:13: __main__: 520: Full AVI Version = 20.1.7-9154-20210916.210140 
INFO: 2023-03-15 23:22:13: __main__: 523: --AVI TEST 2 - Checking health of all Service Engines
INFO: 2023-03-15 23:22:13: __main__: 526: ---- Found 1 Service Engines
INFO: 2023-03-15 23:22:13: __main__: 534: SUCCESS - High Health score of 100.0 for SE, Avi-se-gyhxu
INFO: 2023-03-15 23:22:13: __main__: 537: --AVI TEST 3 - Checking health of AVI Pools 
INFO: 2023-03-15 23:22:13: __main__: 540: ---- Found 7 Avi Pools
INFO: 2023-03-15 23:22:13: __main__: 548: SUCCESS - High Health score of 100.0 for Pool, domain-c8--vmware-system-csi-vsphere-csi-controller-vsphere-csi-controller--2112
INFO: 2023-03-15 23:22:13: __main__: 548: SUCCESS - High Health score of 100.0 for Pool, domain-c8--vmware-system-csi-vsphere-csi-controller-vsphere-csi-controller--2113
INFO: 2023-03-15 23:22:14: __main__: 548: SUCCESS - High Health score of 100.0 for Pool, domain-c8--kube-system-kube-apiserver-lb-svc-kube-apiserver-lb-svc--443
INFO: 2023-03-15 23:22:14: __main__: 548: SUCCESS - High Health score of 100.0 for Pool, domain-c8--kube-system-kube-apiserver-lb-svc-kube-apiserver-lb-svc--6443
INFO: 2023-03-15 23:22:14: __main__: 548: SUCCESS - High Health score of 100.0 for Pool, domain-c8--spvn-infrastructure-control-plane-service-infrastructure-control-plane-service--6443
INFO: 2023-03-15 23:22:14: __main__: 548: SUCCESS - High Health score of 100.0 for Pool, domain-c8--spvn-infrastructure-d194292081d22dbbdc111-infrastructure-d194292081d22dbbdc111--80
INFO: 2023-03-15 23:22:14: __main__: 548: SUCCESS - High Health score of 100.0 for Pool, domain-c8--spvn-infrastructure-2ac9a6d9ed1adaec729a1-infrastructure-2ac9a6d9ed1adaec729a1--3100
INFO: 2023-03-15 23:22:14: __main__: 551: --AVI TEST 4 - Checking health of all Virtual Services 
INFO: 2023-03-15 23:22:14: __main__: 554: ---- Found 5 Virtual Services
INFO: 2023-03-15 23:22:14: __main__: 562: SUCCESS - High Health score of 100.0 for Virtual Service, domain-c8--vmware-system-csi-vsphere-csi-controller
INFO: 2023-03-15 23:22:14: __main__: 562: SUCCESS - High Health score of 100.0 for Virtual Service, domain-c8--kube-system-kube-apiserver-lb-svc
INFO: 2023-03-15 23:22:14: __main__: 562: SUCCESS - High Health score of 100.0 for Virtual Service, domain-c8--spvn-infrastructure-control-plane-service
INFO: 2023-03-15 23:22:15: __main__: 562: SUCCESS - High Health score of 100.0 for Virtual Service, domain-c8--spvn-infrastructure-d194292081d22dbbdc111
INFO: 2023-03-15 23:22:15: __main__: 562: SUCCESS - High Health score of 100.0 for Virtual Service, domain-c8--spvn-infrastructure-2ac9a6d9ed1adaec729a1
INFO: 2023-03-15 23:22:15: __main__: 572: ************ Completed AVI Environment Testing ************

INFO: 2023-03-15 23:22:15: __main__: 574: ************ Beginning K8s Environment Testing ************
INFO: 2023-03-15 23:22:15: __main__: 578: --K8s TEST 1 - Logging into Supervisor Control Plane kube-api server
INFO: 2023-03-15 23:22:15: __main__: 582: ---- SUCCESS - Logged into Supervisor Control Plane kube api-server
INFO: 2023-03-15 23:22:15: __main__: 594: --K8s TEST 2 - Verifying health of all Supervisor Control Plane VMs 
INFO: 2023-03-15 23:22:15: __main__: 598: ---- SUCCESS - Found SC VM SupervisorControlPlaneVM (2) running on ESX host 192.168.100.24
INFO: 2023-03-15 23:22:15: __main__: 598: ---- SUCCESS - Found SC VM SupervisorControlPlaneVM (3) running on ESX host 192.168.100.22
INFO: 2023-03-15 23:22:16: __main__: 598: ---- SUCCESS - Found SC VM SupervisorControlPlaneVM (1) running on ESX host 192.168.100.23
INFO: 2023-03-15 23:22:16: __main__: 600: --K8s TEST 3 - Verifying health of VM's matching CAPI Virtual Machines on Supervisor Cluster. 
INFO: 2023-03-15 23:22:16: __main__: 607: ---- Found 3 kubernetes Workload Cluster VMs
INFO: 2023-03-15 23:22:16: __main__: 623: ---- SUCCESS - Found running VM infrastructure-control-plane-q7pl5 on ESX 192.168.100.26 matching CAPI Machine from a TKC
INFO: 2023-03-15 23:22:16: __main__: 623: ---- SUCCESS - Found running VM infrastructure-np1-h5ngh-76d4bd89f8-8jbvb on ESX 192.168.100.23 matching CAPI Machine from a TKC
INFO: 2023-03-15 23:22:16: __main__: 623: ---- SUCCESS - Found running VM infrastructure-np1-h5ngh-76d4bd89f8-lfxt5 on ESX 192.168.100.26 matching CAPI Machine from a TKC
INFO: 2023-03-15 23:22:16: __main__: 627: ************ Completed K8s Environment Testing ************

 - Successfully Completed Script - Cleaning up REST Session to VC.


```
### NOT IMPLEMENTED YET - Option 2b(Preferred) - Run from a Docker Container on a host with Docker and access to VM Management Network

On any nix machine with Docker already installed.
```
docker run -it --rm -v $HOME:/root -w /usr/src/app mytkrausjr/py3-tz-validate:v7 python tz-validate.py -n vsphere
```
**NOTE:** On systems with SELinux enabled you need to pass an extra mount option "z" to the end of the volume definition in docker run. Without this option you will get a permission error when you run the container.
```
docker run -it --rm -v $HOME:/root:z -w /usr/src/app mytkrausjr/py3-tz-validate:v7 python tz-validate.py -n vsphere
```

