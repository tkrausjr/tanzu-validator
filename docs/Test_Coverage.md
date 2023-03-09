
tz-validate project aims to quickly indentify common misconfigurations and errors in any vSphere with Tanzu environment.  The team is constantly incorporating field feedback to enhance the test coverage. Please open a Gitlab Issue with a FR to add a test that is missing.

## Test Coverage
  ### vSphere with Tanzu
  - [x] The Tag-based storage policy specified exists the vCenter.
  - [ ] Datastores in storage-policy are accessible to all hosts in Cluster
  - [ ] Free Space on Datastores is more than xx %.
  - [x] DNS forward and reverse resolution should work for vCenter and NSX Manager.
  - [x] Ping/curl various network end points that they are reachable (DNS, NTP, VCenter, NSX Manager, )
  - [x] Validate vSphere API is accessible and provided credentials are valid.
  - [x] Validate existence of vSphere cluster specified in configuration YAML is valid.
  - [x] Validate existence of VDS specified in configuration YAML is valid.
  - [x] Validate existence of Datacenter specified in configuration YAML is valid.
  - [x] Validate existence of Cluster specified in configuration YAML is valid.
  - [ ] Validate that HA is enabled on the specified cluster.
  - [ ] Validate that DRS is enabled and set to Fully Automated Mode on the specified cluster.
  - [x] Validate the specified content library is created on the vCenter.
  - [ ] Validate Health of content library.
  - [ ] Validate all images are valid / healthy / policy compliant in Content Library.
  - [x] NTP drift between vCenter and ESXi hosts in Cluster is less than specified max(30 seconds).
  - [ ] AVI Controller liveness probes that check each network connectivity and the frontend VIP IP's
  - [ ] AVI Service Engine Health.
  - [ ] AVI IPAM Address Pool exhaustion
  - [x] K8s - Validate health of Virtual Machines in Supervisor Cluster.
  - [x] K8s - Validate successful Login to Supervisor Cluster K8s API.
  - [x] K8s - Return a list of the CAPI Machine objects tracked by the Supervisor Cluster.
  - [x] K8s - Validate health of Virtual Machines that are part of Tanzu Kubernetes Clusters.
  - [ ] K8s - Return all TKC's API-Server endpoints & Validate K8s API-Server is accessible for all.
  - [ ] SC - Return all TKC's API-Server endpoints & Validate K8s API-Server is accessible for all.
  - [ ] Check PODs in kube-system NS (Containers READY in PODs, STATUS, & RESTARTS)
  - [ ] Check PODs in other system Namespaces such as CSI or AKO
  - [ ] 

  

